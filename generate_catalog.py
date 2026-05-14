import pandas as pd
import math

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
# SOLO CATEGORIAS PRINCIPALES
# ==========================================
df = df[
    df["Categoria Final"]
    .isin([
        "Shoes",
        "Clothing",
        "Accessories"
    ])
]

# ==========================================
# TRM FIJA
# ==========================================
USD_TO_COP = 3750

# ==========================================
# CONFIG
# ==========================================
TAX_USA = 0.07

COSTO_LIBRA_USD = 2.1

MARGEN = 1.1

# ==========================================
# PESO ESTIMADO
# ==========================================
def estimate_weight(row):

    tipo = row.get(
        "Categoria Final",
        ""
    )

    nombre = str(
        row.get("Nombre", "")
    ).lower()

    if tipo == "Shoes":

        if (
            "kids" in nombre
            or "child" in nombre
            or "infant" in nombre
        ):

            return 2

        return 3

    return 2

# ==========================================
# PESO
# ==========================================
df["Peso LB"] = df.apply(
    estimate_weight,
    axis=1
)

# ==========================================
# COBRO CASILLERO
# ==========================================
df["Peso Cobrado"] = (
    df["Peso LB"]
    .apply(lambda x: max(2, math.ceil(x)))
)

# ==========================================
# SHIPPING USD
# ==========================================
df["Shipping USD"] = (
    df["Peso Cobrado"]
    * COSTO_LIBRA_USD
)

# ==========================================
# TAXES USA
# ==========================================
df["Taxes USD"] = (
    df["Precio"] * TAX_USA
)

# ==========================================
# COSTO TOTAL USD
# ==========================================
df["Costo Total USD"] = (
    df["Precio"]
    + df["Taxes USD"]
    + df["Shipping USD"]
)

# ==========================================
# COSTO COP
# ==========================================
df["Costo COP"] = (
    df["Costo Total USD"]
    * USD_TO_COP
)

# ==========================================
# PRECIO VENTA COP
# ==========================================
df["Precio Venta COP"] = (
    df["Costo COP"] * MARGEN
).round(-3)

# ==========================================
# ORDENAR
# ==========================================
df.sort_values(
    by=[
        "Genero",
        "Categoria Final",
        "Precio Venta COP"
    ],
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
onclick="filterProducts('Shoes')">
SHOES
</button>

<button class="filter-btn"
onclick="filterProducts('Clothing')">
CLOTHING
</button>

<button class="filter-btn"
onclick="filterProducts('Accessories')">
ACCESSORIES
</button>

</div>

<div class="grid">
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
        data-tipo="{categoria_final}">

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
# JS FILTROS
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

        const tipo =
        card.dataset.tipo;

        if (
            filter === 'all'
        ) {

            card.classList.remove('hidden');

            return;
        }

        if (
            genero === filter
            ||
            tipo === filter
        ) {

            card.classList.remove('hidden');

        } else {

            card.classList.add('hidden');
        }

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