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
# SHIPPING
# ==========================================
def calculate_shipping(row):

    genero = str(
        row.get("Genero", "")
    ).lower()

    categoria = str(
        row.get("Categoria Final", "")
    ).lower()

    # accesorios
    if categoria == "accessories":

        return 3

    # ropa
    if categoria == "clothing":

        return 5

    # zapatos niños
    if (
        categoria == "shoes"
        and "kids" in genero
    ):

        return 5

    # zapatos adultos
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

.filters-wrapper {

    display: flex;

    justify-content: space-between;

    align-items: center;

    flex-wrap: wrap;

    gap: 20px;

    margin-bottom: 45px;
}

.filters-left,
.filters-right {

    display: flex;

    flex-wrap: wrap;

    gap: 12px;
}

.filter-btn {

    padding: 12px 22px;

    border-radius: 10px;

    border: 1px solid #ddd;

    background: white;

    font-size: 14px;

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

.shipping-info {

    margin-top: 70px;

    background: white;

    border-radius: 16px;

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

    margin-bottom: 8px;
}

.shipping-price {

    color: green;

    font-size: 30px;

    font-weight: bold;
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

    .filters-wrapper {

        flex-direction: column;
    }

}

</style>

</head>

<body>

<h1>CATALOGO ADIDAS</h1>

<div class="subtitle">
Catalogo actualizado automaticamente
</div>

<div class="filters-wrapper">

    <div class="filters-left">

        <button class="filter-btn active"
        onclick="filterProducts('all', this)">
        ALL
        </button>

        <button class="filter-btn"
        onclick="filterProducts('Men', this)">
        MEN
        </button>

        <button class="filter-btn"
        onclick="filterProducts('Women', this)">
        WOMEN
        </button>

        <button class="filter-btn"
        onclick="filterProducts('Kids', this)">
        KIDS
        </button>

        <button class="filter-btn"
        onclick="filterCategory('Clothing', this)">
        ROPA
        </button>

        <button class="filter-btn"
        onclick="filterCategory('Shoes', this)">
        ZAPATOS
        </button>

        <button class="filter-btn"
        onclick="filterCategory('Accessories', this)">
        ACCESORIOS
        </button>

    </div>

    <div class="filters-right">

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

    genero = row.get(
        "Genero",
        ""
    )

    categoria_final = row.get(
        "Categoria Final",
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
        data-categoria="{categoria_final}"
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

function clearButtons(){

    document
    .querySelectorAll('.filter-btn')
    .forEach(btn => {

        btn.classList.remove('active');

    });

}

function filterProducts(filter, button) {

    clearButtons();

    button.classList.add('active');

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

function filterCategory(filter, button){

    clearButtons();

    button.classList.add('active');

    const cards =
    document.querySelectorAll('.card');

    cards.forEach(card => {

        const categoria =
        card.dataset.categoria;

        if (
            categoria === filter
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