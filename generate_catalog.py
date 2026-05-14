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
# SHIPPING NUEVO
# ==========================================
def calculate_shipping(row):

    genero = str(
        row.get("Genero", "")
    ).lower()

    categoria = str(
        row.get("Categoria Final", "")
    ).lower()

    # ======================================
    # ACCESORIOS
    # ======================================
    if categoria == "accessories":

        return 3

    # ======================================
    # ROPA
    # ======================================
    if categoria == "clothing":

        return 5

    # ======================================
    # ZAPATOS NIÑO
    # ======================================
    if (
        categoria == "shoes"
        and "kids" in genero
    ):

        return 5

    # ======================================
    # ZAPATOS ADULTO
    # ======================================
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

    background: #f4f4f4;

    margin: 0;

    padding: 20px;
}

h1 {

    text-align: center;

    margin-bottom: 10px;

    font-size: 52px;
}

.subtitle {

    text-align: center;

    color: gray;

    margin-bottom: 35px;

    font-size: 18px;
}

.filters {

    display: flex;

    flex-wrap: wrap;

    gap: 12px;

    justify-content: center;

    margin-bottom: 45px;
}

.filter-btn {

    padding: 12px 20px;

    border: 1px solid #ddd;

    border-radius: 10px;

    background: white;

    color: black;

    cursor: pointer;

    font-size: 14px;

    font-weight: bold;
}

.filter-btn:hover {

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

    height: 360px;

    background: #f5f5f5;

    display: flex;

    align-items: flex-end;

    justify-content: center;

    padding-bottom: 25px;
}

.image-container img {

    width: 88%;

    height: 88%;

    object-fit: contain;
}

.content {

    padding: 22px;
}

.category {

    font-size: 14px;

    color: gray;

    margin-bottom: 10px;
}

.title {

    font-size: 20px;

    font-weight: bold;

    margin-bottom: 22px;

    min-height: 58px;

    line-height: 1.3;
}

.price {

    font-size: 34px;

    font-weight: bold;

    color: #111;

    margin-top: 10px;

    margin-bottom: 22px;
}

.sizes {

    margin-top: 14px;

    font-size: 16px;

    line-height: 1.7;
}

.footer {

    margin-top: 80px;

    text-align: center;

    color: gray;

    font-size: 14px;
}

.hidden {

    display: none;
}

.shipping-info {

    margin-top: 60px;

    background: white;

    border-radius: 14px;

    padding: 30px;

    display: grid;

    grid-template-columns:
    repeat(auto-fit, minmax(220px, 1fr));

    gap: 20px;

    border: 1px solid #e5e5e5;
}

.shipping-card {

    text-align: center;
}

.shipping-title {

    font-size: 18px;

    font-weight: bold;

    margin-bottom: 10px;
}

.shipping-price {

    color: green;

    font-size: 28px;

    font-weight: bold;
}

</style>
</head>

<body>

<h1>CATALOGO ADIDAS</h1>

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
# FOOTER SHIPPING
# ==========================================
html += """

</div>

<div class="shipping-info">

    <div class="shipping-card">

        <div class="shipping-title">
            ACCESORIOS
        </div>

        <div>
            Envio
        </div>

        <div class="shipping-price">
            $3 USD
        </div>

    </div>

    <div class="shipping-card">

        <div class="shipping-title">
            ZAPATOS KIDS
        </div>

        <div>
            Envio
        </div>

        <div class="shipping-price">
            $5 USD
        </div>

    </div>

    <div class="shipping-card">

        <div class="shipping-title">
            ROPA
        </div>

        <div>
            Envio
        </div>

        <div class="shipping-price">
            $5 USD
        </div>

    </div>

    <div class="shipping-card">

        <div class="shipping-title">
            ZAPATOS MEN / WOMEN
        </div>

        <div>
            Envio
        </div>

        <div class="shipping-price">
            $7 USD
        </div>

    </div>

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