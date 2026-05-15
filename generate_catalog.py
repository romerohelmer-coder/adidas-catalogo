import pandas as pd
import subprocess

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
# FILTRAR PRODUCTOS NO DESEADOS
# ==========================================
exclude_keywords = [

    "sock",
    "socks",

    "shin guard",
    "shin guards",

    "ball",
    "water bottle",
    "bottle",

    "keychain",
    "sticker"
]

df = df[
    ~df["Nombre"]
    .str.lower()
    .str.contains(
        "|".join(exclude_keywords),
        na=False
    )
]

# ==========================================
# CONFIG
# ==========================================
USD_TO_COP = 3750

TAX_USA = 0.07

ADIDAS_DISCOUNT = 0.30

MAX_PROFIT_USD = 35

MIN_PROFIT_USD = 15

MULTIPLIER = 1.8

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

    nombre = str(
        row.get("Nombre", "")
    ).lower()

    # ONE SIZE = ACCESSORIES
    if "one size" in tallas:

        return "Accessories"

    # UNISEX + CLOTHING = ACCESSORIES
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

    # ACCESSORIES
    if categoria == "accessories":

        return 3

    # SLIDES
    if (
        categoria == "shoes"
        and "slides" in nombre
    ):

        return 5

    # CLOTHING
    if categoria == "clothing":

        return 5

    # SHOES KIDS
    if (
        categoria == "shoes"
        and "kids" in genero
    ):

        return 5

    # SHOES ADULT
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
# PRECIO FINAL USD
# ==========================================
df["Precio Final USD"] = (

    df["Costo Total USD"]

    + df["Ganancia USD"]
)

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
html = """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Catalogo Adidas</title>

<style>

body {

    font-family: Arial, sans-serif;

    background: #f5f5f5;

    margin: 0;

    padding: 30px;
}

h1 {

    text-align: center;

    margin-bottom: 10px;

    font-size: 58px;

    font-weight: bold;
}

.subtitle {

    text-align: center;

    color: gray;

    margin-bottom: 40px;

    font-size: 18px;
}

.main-filters {

    display: flex;

    justify-content: center;

    gap: 16px;

    flex-wrap: wrap;

    margin-bottom: 18px;
}

.sub-filters {

    display: flex;

    justify-content: center;

    gap: 14px;

    flex-wrap: wrap;

    margin-bottom: 45px;
}

.filter-btn {

    padding: 12px 24px;

    border-radius: 12px;

    border: 1px solid #ddd;

    background: white;

    font-size: 15px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;
}

.filter-btn:hover {

    background: black;

    color: white;
}

.filter-btn.active {

    background: black;

    color: white;
}

.grid {

    display: grid;

    grid-template-columns:
    repeat(auto-fill, minmax(320px, 1fr));

    gap: 24px;
}

.card {

    background: white;

    border-radius: 14px;

    overflow: hidden;

    border: 1px solid #e5e5e5;

    transition: 0.2s;
}

.card:hover {

    transform: translateY(-4px);
}

.image-container {

    width: 100%;

    height: 380px;

    background: #f3f3f3;

    display: flex;

    align-items: flex-end;

    justify-content: center;

    padding-bottom: 30px;
}

.image-container img {

    width: 88%;

    height: 88%;

    object-fit: contain;
}

.content {

    padding: 24px;
}

.category {

    font-size: 14px;

    color: gray;

    margin-bottom: 12px;
}

.title {

    font-size: 22px;

    font-weight: bold;

    line-height: 1.35;

    min-height: 64px;

    margin-bottom: 24px;
}

.price {

    font-size: 42px;

    font-weight: bold;

    margin-bottom: 22px;
}

.sizes {

    font-size: 16px;

    line-height: 1.8;
}

.hidden {

    display: none;
}

.footer {

    text-align: center;

    margin-top: 60px;

    color: gray;

    font-size: 14px;
}

@media(max-width: 768px){

    h1 {

        font-size: 38px;
    }

}

</style>

</head>

<body>

<h1>CATALOGO ADIDAS</h1>

<div class="subtitle">
Catalogo actualizado automaticamente
</div>

<!-- GENERO -->
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

<!-- CATEGORIA -->
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

<div class="grid" id="productGrid">
"""

# ==========================================
# TARJETAS
# ==========================================
for _, row in df.iterrows():

    genero = row.get(
        "Genero",
        ""
    )

    categoria_final = row.get(
        "Categoria Final",
        ""
    )

    nombre = row.get(
        "Nombre",
        ""
    )

    tallas = row.get(
        "Tallas",
        ""
    )

    imagen = row.get(
        "Imagen",
        ""
    )

    precio_venta_cop = row.get(
        "Precio Venta COP",
        0
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

        </div>

    </div>
    """

    html += card

# ==========================================
# JS
# ==========================================
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

        // genero
        if(
            currentGender !== 'all'
            &&
            genero !== currentGender
        ){

            show = false;
        }

        // categoria
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

Catalogo generado automaticamente<br><br>

Precios en COP. Sujetos a cambios.

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

print("\n================================")
print("CATALOGO GENERADO")
print("index.html")
print("================================")

# ==========================================
# AUTO GIT PUSH
# ==========================================
try:

    print("\n================================")
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

    print("\n================================")
    print("CATALOGO PUBLICADO ONLINE")
    print("================================")

except Exception as e:

    print("\nERROR GIT:", e)