from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import json
import re
import time

from concurrent.futures import ThreadPoolExecutor

# ==========================================
# CONFIG SELENIUM
# ==========================================
options = webdriver.ChromeOptions()

# Adidas funciona mejor SIN headless
options.add_argument("--start-maximized")

# ==========================================
# DRIVER
# ==========================================
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ==========================================
# CONFIG
# ==========================================
BASE_URL = "https://www.adidas.com/us/kids"

VIEW_SIZE = 48

START = 0

all_products = []

all_skus = set()

# ==========================================
# NORMALIZAR CATEGORIAS ADIDAS
# ==========================================
def normalize_category(category):

    category = str(category).strip()

    mapping = {

        "Sportswear": "Sportswear",

        "Originals": "Originals",

        "Running": "Running",

        "Soccer": "Soccer",

        "Basketball": "Basketball",

        "Training": "Training",

        "Outdoor": "Outdoor",

        "Golf": "Golf",

        "Tennis": "Tennis",

        "Skateboarding": "Skateboarding"
    }

    return mapping.get(
        category,
        category
    )

# ==========================================
# EXTRAER PRODUCTS
# ==========================================
def get_products_from_page(url):

    try:

        driver.get(url)

        # Esperar carga
        time.sleep(6)

        # Scroll
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        time.sleep(2)

        html = driver.page_source

        print("\nHTML LENGTH:", len(html))

        # ==================================
        # NEXT DATA
        # ==================================
        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html,
            re.DOTALL
        )

        if not match:

            print("\n================================")
            print("NO NEXT DATA")
            print("================================")

            return []

        next_data = match.group(1)

        print("\n================================")
        print("NEXT DATA OK")
        print("================================")

        data = json.loads(next_data)

        products = (
            data["props"]
            ["pageProps"]
            ["products"]
        )

        return products

    except Exception as e:

        print("ERROR PAGE:", e)

        return []

# ==========================================
# API TALLAS
# ==========================================
def get_sizes(sku):

    api_url = (
        f"https://www.adidas.com/api/products/"
        f"{sku}/availability?sitePath=us"
    )

    try:

        result = driver.execute_async_script("""

            const url = arguments[0];

            const callback = arguments[1];

            fetch(url)
                .then(response => {

                    return response.text()
                        .then(text => {

                            callback({
                                status: response.status,
                                text: text
                            });

                        });

                })
                .catch(error => {

                    callback({
                        status: 500,
                        text: error.toString()
                    });

                });

        """, api_url)

        print(
            "SIZE API:",
            sku,
            result["status"]
        )

        if result["status"] != 200:

            return {

                "sizes": "",

                "sizes_count": 0,

                "stock": "",

                "availability": ""
            }

        data = json.loads(
            result["text"]
        )

        variation_list = data.get(
            "variation_list",
            []
        )

        sizes = []

        stock = []

        availability = []

        for item in variation_list:

            status = item.get(
                "availability_status",
                ""
            )

            if status != "IN_STOCK":
                continue

            size = item.get(
                "size",
                ""
            )

            qty = item.get(
                "availability",
                ""
            )

            sizes.append(str(size))

            stock.append(
                f"{size}:{qty}"
            )

            availability.append(
                f"{size}:{status}"
            )

        return {

            "sizes": ", ".join(sizes),

            "sizes_count": len(sizes),

            "stock": " | ".join(stock),

            "availability": " | ".join(availability)
        }

    except Exception as e:

        print("ERROR TALLAS:", sku, e)

        return {

            "sizes": "",

            "sizes_count": 0,

            "stock": "",

            "availability": ""
        }

# ==========================================
# DEAL SCORE
# ==========================================
def calculate_score(row):

    score = 0

    # ======================================
    # DESCUENTO
    # ======================================
    try:

        discount = abs(
            int(row["Descuento"])
        )

        if discount >= 70:
            score += 50

        elif discount >= 50:
            score += 40

        elif discount >= 40:
            score += 30

        elif discount >= 30:
            score += 20

    except:
        pass

    # ======================================
    # TALLAS
    # ======================================
    try:

        sizes_count = int(
            row["Cantidad Tallas"]
        )

        if sizes_count >= 8:
            score += 25

        elif sizes_count >= 5:
            score += 15

        elif sizes_count >= 3:
            score += 10

    except:
        pass

    # ======================================
    # RATING
    # ======================================
    try:

        rating = float(
            row["Rating"]
        )

        if rating >= 4.8:
            score += 20

        elif rating >= 4.5:
            score += 15

        elif rating >= 4:
            score += 10

    except:
        pass

    # ======================================
    # REVIEWS
    # ======================================
    try:

        reviews = int(
            row["Reviews"]
        )

        if reviews >= 1000:
            score += 20

        elif reviews >= 300:
            score += 15

        elif reviews >= 100:
            score += 10

    except:
        pass

    # ======================================
    # MODELOS POPULARES
    # ======================================
    nombre = str(
        row["Nombre"]
    ).lower()

    hype_keywords = [

        "samba",

        "gazelle",

        "campus",

        "handball",

        "superstar"
    ]

    for keyword in hype_keywords:

        if keyword in nombre:

            score += 15

            break

    return score

# ==========================================
# PROCESAR PRODUCTO
# ==========================================
def process_product(p):

    try:

        sku = p.get("id", "")

        if not sku:

            return None

        nombre = p.get(
            "title",
            ""
        )

        subtitle = p.get(
            "subTitle",
            ""
        )

        # ==================================
        # CATEGORIA ADIDAS
        # ==================================
        categoria = normalize_category(
            p.get(
                "category",
                ""
            )
        )

        link = p.get(
            "url",
            ""
        )

        image = p.get(
            "image",
            ""
        )

        hover_image = p.get(
            "hoverImage",
            ""
        )

        rating = p.get(
            "rating",
            ""
        )

        rating_count = p.get(
            "ratingCount",
            ""
        )

        badges = p.get(
            "badges",
            []
        )

        badges_text = ", ".join([
            b.get("text", "")
            for b in badges
        ])

        # ==================================
        # PRECIOS
        # ==================================
        sale_price = ""

        original_price = ""

        discount = ""

        price_data = p.get(
            "priceData",
            {}
        )

        prices = price_data.get(
            "prices",
            []
        )

        for price in prices:

            tipo = price.get(
                "type",
                ""
            )

            value = price.get(
                "value",
                ""
            )

            if tipo == "sale":

                sale_price = value

            elif tipo == "original":

                original_price = value

                discount = price.get(
                    "discountPercentage",
                    ""
                )

        if sale_price == "":
            sale_price = original_price

        sold_out = price_data.get(
            "isSoldOut",
            False
        )

        colors = len(
            p.get(
                "colourVariations",
                []
            )
        )

        # ==================================
        # TALLAS
        # ==================================
        sizes_data = get_sizes(sku)

        print("--------------------------------")
        print(nombre)
        print("Categoria:", categoria)
        print("SKU:", sku)
        print("Precio:", sale_price)
        print("Tallas:", sizes_data["sizes"])

        return {

            "Categoria": categoria,

            "SKU": sku,

            "Nombre": nombre,

            "Subtitulo": subtitle,

            "Precio": sale_price,

            "Precio Original": original_price,

            "Descuento": discount,

            "Rating": rating,

            "Reviews": rating_count,

            "Colores": colors,

            "Badges": badges_text,

            "Sold Out": sold_out,

            "Tallas": sizes_data["sizes"],

            "Cantidad Tallas": sizes_data["sizes_count"],

            "Stock": sizes_data["stock"],

            "Availability": sizes_data["availability"],

            "Imagen": image,

            "Hover Imagen": hover_image,

            "Link": link
        }

    except Exception as e:

        print("ERROR PRODUCT:", e)

        return None

# ==========================================
# LOOP PAGINAS
# ==========================================
while True:

    url = f"{BASE_URL}?start={START}"

    print("\n================================")
    print("URL:", url)
    print("================================")

    products = get_products_from_page(url)

    if not products:

        print("\n================================")
        print("NO HAY MAS PRODUCTOS")
        print("================================")

        break

    print("\nPRODUCTOS:", len(products))

    # ======================================
    # FILTRAR DUPLICADOS
    # ======================================
    new_products = []

    for p in products:

        sku = p.get("id", "")

        if sku in all_skus:
            continue

        all_skus.add(sku)

        new_products.append(p)

    # ======================================
    # MULTITHREADING
    # ======================================
    with ThreadPoolExecutor(max_workers=10) as executor:

        results = list(
            executor.map(
                process_product,
                new_products
            )
        )

    # ======================================
    # SAVE RESULTS
    # ======================================
    for result in results:

        if result:

            all_products.append(result)

    # ======================================
    # DATAFRAME TEMP
    # ======================================
    temp_df = pd.DataFrame(all_products)

    temp_df.drop_duplicates(
        subset=["SKU"],
        inplace=True
    )

    # ======================================
    # SCORE TEMP
    # ======================================
    temp_df["Deal Score"] = temp_df.apply(
        calculate_score,
        axis=1
    )

    temp_df.sort_values(
        by="Deal Score",
        ascending=False,
        inplace=True
    )

    # ======================================
    # GUARDADO INCREMENTAL
    # ======================================
    temp_df.to_excel(
        "adidas_incremental.xlsx",
        index=False
    )

    print("\n================================")
    print("TOTAL:", len(temp_df))
    print("GUARDADO INCREMENTAL")
    print("================================")

    START += VIEW_SIZE

# ==========================================
# CLOSE
# ==========================================
driver.quit()

# ==========================================
# DATAFRAME FINAL
# ==========================================
df = pd.DataFrame(all_products)

df.drop_duplicates(
    subset=["SKU"],
    inplace=True
)

# ==========================================
# DEAL SCORE FINAL
# ==========================================
df["Deal Score"] = df.apply(
    calculate_score,
    axis=1
)

# ==========================================
# ORDENAR
# ==========================================
df.sort_values(
    by="Deal Score",
    ascending=False,
    inplace=True
)

# ==========================================
# EXPORT FINAL
# ==========================================
file_name = "adidas_enterprise_final.xlsx"

df.to_excel(
    file_name,
    index=False
)

# ==========================================
# FINAL
# ==========================================
print("\n================================")
print("SCRAPING FINALIZADO")
print("TOTAL PRODUCTOS:", len(df))
print("ARCHIVO:", file_name)
print("================================")