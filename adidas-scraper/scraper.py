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
BASE_URL = "https://www.adidas.com/us/shop?grid=true&sort=top-sellers"

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
# CLASIFICAR GENERO
# ==========================================
def classify_gender(nombre, subtitle, url):

    text = f"""
    {nombre}
    {subtitle}
    {url}
    """.lower()

    if (
        "women" in text
        or "female" in text
        or "/women-" in text
    ):

        return "Women"

    if (
        "men" in text
        or "male" in text
        or "/men-" in text
    ):

        return "Men"

    if (
        "kids" in text
        or "child" in text
        or "infant" in text
        or "/kids-" in text
    ):

        return "Kids"

    return "Unisex"

# ==========================================
# CLASIFICAR PRODUCTO
# USANDO URL OFICIAL ADIDAS
# ==========================================
def classify_product(url):

    text = str(url).lower()

    # ======================================
    # SHOES
    # ======================================
    shoes_keywords = [

        "-shoes",
        "-slides",
        "-sandals",
        "-cleats",
        "-boots"
    ]

    for word in shoes_keywords:

        if word in text:

            return "Shoes"

    # ======================================
    # ACCESSORIES
    # ======================================
    accessories_keywords = [

        "-backpack",
        "-bag",
        "-cap",
        "-hat",
        "-socks",
        "-gloves",
        "-ball",
        "-belt",
        "-bottle"
    ]

    for word in accessories_keywords:

        if word in text:

            return "Accessories"

    # ======================================
    # CLOTHING
    # ======================================
    return "Clothing"

# ==========================================
# EXTRAER PRODUCTS
# ==========================================
def get_products_from_page(url):

    try:

        driver.get(url)

        time.sleep(6)

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        time.sleep(2)

        html = driver.page_source

        print("\nHTML LENGTH:", len(html))

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

        if result["status"] != 200:

            return {

                "sizes": "",

                "sizes_count": 0
            }

        data = json.loads(
            result["text"]
        )

        variation_list = data.get(
            "variation_list",
            []
        )

        sizes = []

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

            sizes.append(str(size))

        return {

            "sizes": ", ".join(sizes),

            "sizes_count": len(sizes)
        }

    except Exception as e:

        print("ERROR TALLAS:", sku, e)

        return {

            "sizes": "",

            "sizes_count": 0
        }

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

        # ==================================
        # LINK
        # ==================================
        link = p.get(
            "url",
            ""
        )

        # ==================================
        # GENERO
        # ==================================
        genero = classify_gender(
            nombre,
            subtitle,
            link
        )

        # ==================================
        # CATEGORIA FINAL
        # ==================================
        categoria_final = classify_product(
            link
        )

        # ==================================
        # IMAGEN
        # ==================================
        image = p.get(
            "image",
            ""
        )

        # ==================================
        # IMAGEN HD
        # ==================================
        image = (
            image
            .replace(
                "w_280,h_280",
                "w_1200,h_1200"
            )
            .replace(
                "w_320,h_320",
                "w_1200,h_1200"
            )
            .replace(
                "w_600",
                "w_1200"
            )
        )

        # ==================================
        # RATING
        # ==================================
        rating = p.get(
            "rating",
            ""
        )

        rating_count = p.get(
            "ratingCount",
            ""
        )

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

        # ==================================
        # COLORES
        # ==================================
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
        print("Genero:", genero)
        print("Tipo:", categoria_final)
        print("Categoria:", categoria)
        print("SKU:", sku)
        print("Precio:", sale_price)
        print("Tallas:", sizes_data["sizes"])

        return {

            "Genero": genero,

            "Categoria Final": categoria_final,

            "Categoria Adidas": categoria,

            "SKU": sku,

            "Nombre": nombre,

            "Subtitulo": subtitle,

            "Precio": sale_price,

            "Precio Original": original_price,

            "Descuento": discount,

            "Rating": rating,

            "Reviews": rating_count,

            "Colores": colors,

            "Sold Out": sold_out,

            "Tallas": sizes_data["sizes"],

            "Cantidad Tallas": sizes_data["sizes_count"],

            "Imagen": image,

            "Link": link
        }

    except Exception as e:

        print("ERROR PRODUCT:", e)

        return None

# ==========================================
# LOOP PAGINAS
# ==========================================
while True:

    url = f"{BASE_URL}&start={START}"

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

    new_products = []

    for p in products:

        sku = p.get("id", "")

        if sku in all_skus:
            continue

        all_skus.add(sku)

        new_products.append(p)

    with ThreadPoolExecutor(max_workers=10) as executor:

        results = list(
            executor.map(
                process_product,
                new_products
            )
        )

    for result in results:

        if result:

            all_products.append(result)

    temp_df = pd.DataFrame(all_products)

    temp_df.drop_duplicates(
        subset=["SKU"],
        inplace=True
    )

    temp_df.to_excel(
        "adidas_shop_incremental.xlsx",
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
# ORDENAR
# ==========================================
df.sort_values(
    by=[
        "Genero",
        "Categoria Final",
        "Precio"
    ],
    ascending=True,
    inplace=True
)

# ==========================================
# EXPORT FINAL
# ==========================================
file_name = "adidas_shop_final.xlsx"

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