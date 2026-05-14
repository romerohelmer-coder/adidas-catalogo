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

    # medias
    "sock",
    "socks",

    # futbol accesorios
    "shin guard",
    "shin guards",

    # accesorios varios
    "ball",
    "water bottle",
    "bottle",
    "glove",
    "belt",
    "headband",
    "wristband",

    # gym pequeños
    "mat",
    "roller",

    # otros
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
# TRM FIJA
# ==========================================
USD_TO_COP = 3750

# ==========================================
# CONFIG
# ==========================================
TAX_USA = 0.07

# Adidas coupon
ADIDAS_DISCOUNT = 0.30

# Tope ganancia
MAX_PROFIT_USD = 35

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
def calculate_shipping(genero):

    genero = str(genero).lower()

    # niños
    if "kids" in genero:

        return 5

    # adultos
    return 7

df["Shipping USD"] = df["Genero"].apply(
    calculate_shipping
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

    profit = total_usd

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
# HTML INICIO
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

    background: #f4f4f4;

    margin: 0;

    padding: 20px;
}

h1 {

    text-align: center;

    margin-bottom: 10px;
}

.subtitle {

    text-align: center;

    color: gray;

    margin-bottom: 30px;
}

.filters {

    display: flex;

    flex-wrap: wrap;

    gap: 10px;

    justify-content: center;

    margin-bottom: 40px;
}

.filter-btn {

    padding: 10px 18px;

    border: none;

    border-radius: 8px;

    background: black;

    color: white;

    cursor: pointer;

    font-size: 14px;
}

.filter-btn:hover {

    opacity: 0.85;
}

.grid {

    display: grid;

    grid-template-columns:
    repeat(auto-fill, minmax(280px, 1fr));

    gap: 20px;
}

.card {

    background: white;

    border-radius: 12px;

    overflow: hidden;

    box-shadow: 0 2px 10px rgba(0,0,0,0.1);

    transition: 0.2s;
}

.card:hover {

    transform: translateY(-4px);
}

.image-container {

    width: 100%;

    height: 280px;

    background: #fff;

    display: flex;

    align-items: center;

    justify-content: center;
}

.image-container img {

    width: 100%;

    height: 100%;

    object-fit: cover;
}

.content {

    padding: 15px;
}

.category {

    font-size: 12px;

    color: gray;

    margin-bottom: 5px;
}

.title {

    font-size: 18px;

    font-weight: bold;

    margin-bottom: 10px;

    min-height: 48px;
}

.price {

    font-size: 28px;

    font-weight: bold;

    color: #111;

    margin-top: 10px;
}

.sizes {

    margin-top: 12px;

    font-size: 14px;

    line-height: 1.5;
}

.footer {

    margin-top: 70px;

    text-align: center;

    color: gray;

    font-size: 12px;
}

.hidden {

    display: none;
}

</style>
</head>

<body>

<h1>Catalogo Adidas</h1>

<div class="subtitle">
Catalogo actualizado automaticamente
</div>

<div class="filters">

<button class="filter-btn"
onclick="filterProducts('all')">
ALL
</button>

<button class="filter-btn"
onclick="filterProducts('Men')">
MEN
</button>

<button class="filter-btn"
onclick="filterProducts('Women')">
WOMEN
</button>

<button class="filter-btn"
onclick="filterProducts('Kids')">
KIDS
</button>

<button class="filter-btn"
onclick="sortProducts('asc')">
PRECIO ↑
</button>

<button class="filter-btn"
onclick="sortProducts('desc')">
PRECIO ↓
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

    categoria = row.get(
        "Categoria Adidas",
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
        data-price="{precio_venta_cop}">

        <div class="image-container">
            <img src="{imagen}" alt="{nombre}">
        </div>

        <div class="content">

            <div class="category">
                {genero} | {categoria}
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

function filterProducts(filter) {

    const cards =
    document.querySelectorAll('.card');

    cards.forEach(card => {

        const genero =
        card.dataset.genero;

        if (
            filter === 'all'
        ) {

            card.classList.remove('hidden');

            return;
        }

        if (
            genero === filter
        ) {

            card.classList.remove('hidden');

        } else {

            card.classList.add('hidden');
        }

    });

}

function sortProducts(order) {

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

        if (order === 'asc') {

            return priceA - priceB;

        } else {

            return priceB - priceA;
        }

    });

    cards.forEach(card => {

        grid.appendChild(card);

    });

}

</script>

<div class="footer">
Catalogo generado automaticamente
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