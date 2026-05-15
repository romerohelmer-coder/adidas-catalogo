import pandas as pd
import subprocess
import base64

# ==========================================
# LEER EXCEL
# ==========================================
df = pd.read_excel(
    "adidas-scraper/adidas_shop_final.xlsx"
)

# ==========================================
# LIMPIAR
# ==========================================
df = df.fillna("")

# ==========================================
# ELIMINAR SIN STOCK
# ==========================================
df = df[
    df["Tallas"]
    .astype(str)
    .str.strip()
    != ""
]

# ==========================================
# FILTRAR PRODUCTOS NO DESEADOS
# ==========================================
exclude_keywords = [

    "sock",
    "socks",

    "cushioned",

    "shin guard",
    "shin guards",

    "ball",
    "water bottle",
    "bottle",

    "keychain",
    "sticker"
]

# ==========================================
# FILTRO AVANZADO
# ==========================================
df = df[
    ~df["Nombre"]
    .astype(str)
    .str.lower()
    .str.contains(
        "|".join(exclude_keywords),
        na=False,
        regex=True
    )
]

# ==========================================
# ELIMINAR CUSHIONED
# ==========================================
df = df[
    ~df["Nombre"]
    .astype(str)
    .str.contains(
        "Cushioned",
        case=False,
        na=False
    )
]

# ==========================================
# LOGO BASE64
# ==========================================
with open(
    "logo.jpg",
    "rb"
) as image_file:

    logo_base64 = base64.b64encode(
        image_file.read()
    ).decode("utf-8")

# ==========================================
# CONFIG
# ==========================================
USD_TO_COP = 3750

TAX_USA = 0.07

ADIDAS_DISCOUNT = 0.30

MAX_PROFIT_USD = 35

MIN_PROFIT_USD = 15

MULTIPLIER = 1.7

# ==========================================
# LIMPIAR PRECIO
# ==========================================
df["Precio"] = pd.to_numeric(
    df["Precio"],
    errors="coerce"
)

df = df[
    df["Precio"].notnull()
]

# ==========================================
# AJUSTAR CATEGORIAS
# ==========================================
def adjust_category(row):

    categoria = str(
        row.get("Categoria Final", "")
    )

    genero = str(
        row.get("Genero", "")
    ).lower()

    tallas = str(
        row.get("Tallas", "")
    ).lower()

    if "one size" in tallas:

        return "Accessories"

    if (
        genero == "unisex"
        and categoria == "Clothing"
    ):

        return "Accessories"

    return categoria

df["Categoria Final"] = df.apply(
    adjust_category,
    axis=1
)

# ==========================================
# DESCUENTO ADIDAS
# ==========================================
df["Precio Descuento USD"] = (
    df["Precio"]
    * (1 - ADIDAS_DISCOUNT)
)

# ==========================================
# TAXES USA
# ==========================================
df["Taxes USD"] = (
    df["Precio Descuento USD"]
    * TAX_USA
)

# ==========================================
# SHIPPING
# ==========================================
def calculate_shipping(row):

    genero = str(
        row.get("Genero", "")
    ).lower()

    categoria = str(
        row.get("Categoria Final", "")
    ).lower()

    nombre = str(
        row.get("Nombre", "")
    ).lower()

    if categoria == "accessories":

        return 3

    if (
        categoria == "shoes"
        and "slides" in nombre
    ):

        return 5

    if categoria == "clothing":

        return 5

    if (
        categoria == "shoes"
        and "kids" in genero
    ):

        return 5

    if categoria == "shoes":

        return 7

    return 5

df["Shipping USD"] = df.apply(
    calculate_shipping,
    axis=1
)

# ==========================================
# COSTO TOTAL USD
# ==========================================
df["Costo Total USD"] = (

    df["Precio Descuento USD"]

    + df["Taxes USD"]

    + df["Shipping USD"]
)

# ==========================================
# GANANCIA
# ==========================================
def calculate_profit(total_usd):

    profit = (
        total_usd
        * (MULTIPLIER - 1)
    )

    if profit < MIN_PROFIT_USD:

        profit = MIN_PROFIT_USD

    if profit > MAX_PROFIT_USD:

        profit = MAX_PROFIT_USD

    return profit

df["Ganancia USD"] = (
    df["Costo Total USD"]
    .apply(calculate_profit)
)

# ==========================================
# PRECIO FINAL
# ==========================================
df["Precio Final USD"] = (

    df["Costo Total USD"]

    + df["Ganancia USD"]
)

# ==========================================
# FILTRO SLIDES > 42 USD
# ==========================================
df = df[
    ~(
        df["Nombre"]
        .astype(str)
        .str.contains(
            "slides",
            case=False,
            na=False
        )
        &
        (
            df["Precio Final USD"] > 42
        )
    )
]

# ==========================================
# PRECIO FINAL COP
# ==========================================
df["Precio Venta COP"] = (

    df["Precio Final USD"]

    * USD_TO_COP

).round(-3)

# ==========================================
# ORDENAR
# ==========================================
df.sort_values(
    by="Precio Venta COP",
    ascending=True,
    inplace=True
)

# ==========================================
# HTML
# ==========================================
html = f"""
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Saroma Store</title>

<style>

body {{

    font-family: Arial, sans-serif;

    background:
    linear-gradient(
        to bottom,
        #f9f6ef,
        #f5f1e8
    );

    margin: 0;

    padding: 30px;

    color: #2d2d2d;
}}

.header {{

    text-align: center;

    margin-bottom: 30px;
}}

.logo {{

    width: 260px;

    max-width: 80%;

    opacity: 0.96;

    margin-bottom: 12px;
}}

.subtitle {{

    color: #8a7a55;

    font-size: 16px;

    letter-spacing: 1px;

    margin-bottom: 35px;
}}

.filters-sticky {{

    position: sticky;

    top: 0;

    z-index: 999;

    background:
    rgba(249,246,239,0.96);

    backdrop-filter: blur(10px);

    padding-top: 14px;

    padding-bottom: 18px;

    border-bottom:
    1px solid #e9dfcb;

    margin-bottom: 35px;
}}

.main-filters,
.sub-filters {{

    display: flex;

    justify-content: center;

    gap: 14px;

    flex-wrap: wrap;
}}

.main-filters {{

    margin-bottom: 16px;
}}

.filter-btn {{

    padding: 12px 24px;

    border-radius: 30px;

    border: 1px solid #d8c7a2;

    background: white;

    color: #8a6b2f;

    font-size: 14px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.25s;
}}

.filter-btn:hover {{

    background: #b9975b;

    color: white;
}}

.filter-btn.active {{

    background: #b9975b;

    color: white;

    border-color: #b9975b;
}}

.grid {{

    display: grid;

    grid-template-columns:
    repeat(auto-fill, minmax(320px, 1fr));

    gap: 26px;
}}

.card {{

    background: white;

    border-radius: 24px;

    overflow: hidden;

    border:
    1px solid #eadfcb;

    transition: 0.25s;

    box-shadow:
    0 8px 25px rgba(0,0,0,0.04);
}}

.card:hover {{

    transform: translateY(-5px);

    box-shadow:
    0 14px 34px rgba(0,0,0,0.08);
}}

.image-container {{

    width: 100%;

    height: 380px;

    background:
    linear-gradient(
        to bottom,
        #f8f6f2,
        #f1ede5
    );

    display: flex;

    align-items: flex-end;

    justify-content: center;

    padding-bottom: 26px;
}}

.image-container img {{

    width: 94%;

    height: 94%;

    object-fit: contain;
}}

.content {{

    padding: 26px;
}}

.category {{

    font-size: 13px;

    color: #9a8762;

    margin-bottom: 12px;
}}

.title {{

    font-size: 22px;

    font-weight: bold;

    line-height: 1.35;

    min-height: 64px;

    margin-bottom: 24px;

    color: #2b2b2b;
}}

.price {{

    font-size: 40px;

    font-weight: bold;

    margin-bottom: 20px;

    color: #9a6f20;
}}

.sizes {{

    font-size: 15px;

    line-height: 1.8;

    color: #444;
}}

.buy-btn {{

    display: block;

    margin-top: 18px;

    text-align: center;

    background: #b9975b;

    color: white;

    text-decoration: none;

    padding: 14px;

    border-radius: 14px;

    font-weight: bold;

    transition: 0.25s;
}}

.buy-btn:hover {{

    background: #9d7d42;
}}

.hidden {{

    display: none;
}}

.footer {{

    text-align: center;

    margin-top: 70px;

    color: #9a8762;

    font-size: 13px;
}}

@media(max-width: 768px){{

    body {{
        padding: 12px;
    }}

    .logo {{
        width: 170px;
    }}

    .grid {{
        grid-template-columns:
        repeat(2, 1fr);

        gap: 12px;
    }}

    .image-container {{
        height: 220px;
    }}

    .title {{
        font-size: 15px;

        min-height: 42px;
    }}

    .price {{
        font-size: 22px;
    }}

}}

</style>

</head>

<body>

<div class="header">

    <img
    class="logo"
    src="data:image/jpeg;base64,{logo_base64}">

    <div class="subtitle">
        Catalogo Adidas
    </div>

</div>

<div class="filters-sticky">

    <div class="main-filters">

        <button class="filter-btn active"
        onclick="setGender('all', this)">
        ALL
        </button>

        <button class="filter-btn"
        onclick="setGender('Men', this)">
        MEN
        </button>

        <button class="filter-btn"
        onclick="setGender('Women', this)">
        WOMEN
        </button>

        <button class="filter-btn"
        onclick="setGender('Kids', this)">
        KIDS
        </button>

    </div>

    <div class="sub-filters">

        <button class="filter-btn active"
        onclick="setCategory('Shoes', this)">
        ZAPATOS
        </button>

        <button class="filter-btn"
        onclick="setCategory('Clothing', this)">
        ROPA
        </button>

        <button class="filter-btn"
        onclick="setCategory('Accessories', this)">
        ACCESORIOS
        </button>

        <button class="filter-btn"
        onclick="sortProducts('asc')">
        ⬆ PRECIO
        </button>

        <button class="filter-btn"
        onclick="sortProducts('desc')">
        PRECIO ⬇
        </button>

    </div>

</div>

<div class="grid" id="productGrid">
"""

# ==========================================
# TARJETAS
# ==========================================
for _, row in df.iterrows():

    genero = row.get("Genero", "")
    categoria_final = row.get("Categoria Final", "")
    nombre = row.get("Nombre", "")
    tallas = row.get("Tallas", "")
    imagen = row.get("Imagen", "")
    precio_venta_cop = row.get("Precio Venta COP", 0)

    short_image = imagen

    if "?" in short_image:
        short_image = short_image.split("?")[0]

    whatsapp_text = f'''
Buen día, deseo pedir el siguiente producto.

Producto:
{nombre}

Imagen:
{short_image}
'''

    whatsapp_text = whatsapp_text.replace(
        "\\n",
        "%0A"
    )

    card = f"""
    <div class="card"
        data-genero="{genero}"
        data-categoria="{categoria_final}"
        data-price="{precio_venta_cop}">

        <div class="image-container">
            <img src="{imagen}" alt="{nombre}">
        </div>

        <div class="content">

            <div class="category">
                {genero} | {categoria_final}
            </div>

            <div class="title">
                {nombre}
            </div>

            <div class="price">
                ${int(precio_venta_cop):,} COP
            </div>

            <div class="sizes">
                <strong>Tallas:</strong><br>
                {tallas}
            </div>

            <a
            class="buy-btn"
            href="https://wa.me/573105706630?text={whatsapp_text}"
            target="_blank">

            Solicitar Pedido

            </a>

        </div>

    </div>
    """

    html += card

html += """

</div>

<script>

let currentGender = 'all';
let currentCategory = 'Shoes';

function refreshProducts(){

    const cards =
    document.querySelectorAll('.card');

    cards.forEach(card => {

        const genero =
        card.dataset.genero;

        const categoria =
        card.dataset.categoria;

        let show = true;

        if(
            currentGender !== 'all'
            &&
            genero !== currentGender
        ){
            show = false;
        }

        if(
            categoria !== currentCategory
        ){
            show = false;
        }

        if(show){
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }

    });

}

function clearMainButtons(){

    document
    .querySelectorAll('.main-filters .filter-btn')
    .forEach(btn => {
        btn.classList.remove('active');
    });

}

function clearSubButtons(){

    document
    .querySelectorAll('.sub-filters .filter-btn')
    .forEach(btn => {
        btn.classList.remove('active');
    });

}

function setGender(gender, button){

    currentGender = gender;

    clearMainButtons();

    button.classList.add('active');

    refreshProducts();

}

function setCategory(category, button){

    currentCategory = category;

    clearSubButtons();

    button.classList.add('active');

    refreshProducts();

}

function sortProducts(order){

    const grid =
    document.getElementById('productGrid');

    const cards =
    Array.from(
        document.querySelectorAll('.card')
    );

    cards.sort((a, b) => {

        const priceA =
        parseFloat(a.dataset.price);

        const priceB =
        parseFloat(b.dataset.price);

        if(order === 'asc'){
            return priceA - priceB;
        } else {
            return priceB - priceA;
        }

    });

    cards.forEach(card => {
        grid.appendChild(card);
    });

}

refreshProducts();

</script>

<div class="footer">

Saroma Store © 2026<br>
Catalogo Adidas

</div>

</body>
</html>
"""

# ==========================================
# GUARDAR HTML
# ==========================================
with open(
    "index.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(html)

print("\\n================================")
print("CATALOGO GENERADO")
print("index.html")
print("================================")

# ==========================================
# AUTO GIT PUSH
# ==========================================
try:

    print("\\n================================")
    print("SUBIENDO A GITHUB")
    print("================================")

    subprocess.run(
        ["git", "add", "."],
        check=True
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "catalogo auto update"
        ],
        check=False
    )

    subprocess.run(
        ["git", "push"],
        check=True
    )

    print("\\n================================")
    print("CATALOGO PUBLICADO ONLINE")
    print("================================")

except Exception as e:

    print("\\nERROR GIT:", e)