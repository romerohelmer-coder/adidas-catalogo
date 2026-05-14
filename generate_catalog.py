import pandas as pd

# ==========================================
# LEER EXCEL
# ==========================================
df = pd.read_excel(
    "adidas-scraper/adidas_enterprise_final.xlsx"
)

# ==========================================
# LIMPIAR
# ==========================================
df = df.fillna("")

# ==========================================
# ORDENAR
# ==========================================
df.sort_values(
    by="Deal Score",
    ascending=False,
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

<meta name="viewport" content="width=device-width, initial-scale=1.0">

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

    margin-bottom: 30px;
}

.grid {

    display: grid;

    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));

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

    font-size: 22px;

    font-weight: bold;

    color: #111;
}

.original {

    text-decoration: line-through;

    color: gray;

    margin-left: 10px;
}

.discount {

    color: red;

    font-weight: bold;

    margin-top: 5px;
}

.sizes {

    margin-top: 10px;

    font-size: 14px;
}

.score {

    margin-top: 10px;

    font-size: 14px;

    font-weight: bold;

    color: green;
}

.button {

    display: inline-block;

    margin-top: 15px;

    padding: 10px 15px;

    background: black;

    color: white;

    text-decoration: none;

    border-radius: 8px;
}

.button:hover {

    opacity: 0.9;
}

</style>
</head>

<body>

<h1>Catalogo Adidas</h1>

<div class="grid">
"""

# ==========================================
# GENERAR TARJETAS
# ==========================================
for _, row in df.iterrows():

    categoria = row.get("Categoria", "")

    nombre = row.get("Nombre", "")

    precio = row.get("Precio", "")

    original = row.get("Precio Original", "")

    descuento = row.get("Descuento", "")

    tallas = row.get("Tallas", "")

    imagen = row.get("Imagen", "")

    link = row.get("Link", "")

    score = row.get("Deal Score", "")

    card = f"""
    <div class="card">

        <div class="image-container">
            <img src="{imagen}" alt="{nombre}">
        </div>

        <div class="content">

            <div class="category">
                {categoria}
            </div>

            <div class="title">
                {nombre}
            </div>

            <div class="price">
                ${precio}

                <span class="original">
                    ${original}
                </span>
            </div>

            <div class="discount">
                {descuento}% OFF
            </div>

            <div class="sizes">
                <strong>Tallas:</strong><br>
                {tallas}
            </div>

            <div class="score">
                Deal Score: {score}
            </div>

            <a class="button" href="{link}" target="_blank">
                Ver Producto
            </a>

        </div>

    </div>
    """

    html += card

# ==========================================
# CIERRE HTML
# ==========================================
html += """
</div>

</body>
</html>
"""

# ==========================================
# GUARDAR HTML
# ==========================================
with open(
    "catalogo_adidas.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(html)

print("\n================================")
print("CATALOGO GENERADO")
print("catalogo_adidas.html")
print("================================")