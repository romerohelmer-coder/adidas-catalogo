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
# FILTROS PRODUCTOS
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
# LOGO
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
# PRECIO NUMERICO
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
# DESCUENTO
# ==========================================
df["Precio Descuento USD"] = (
    df["Precio"]
    * (1 - ADIDAS_DISCOUNT)
)

# ==========================================
# TAXES
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
# COSTO TOTAL
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
# FILTRO SLIDES
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

<title>Catalogo Adidas</title>

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

    padding: 20px;

    color: #2d2d2d;
}}

.header {{

    text-align: center;

    margin-bottom: 30px;
}}

.logo {{

    width: 240px;

    max-width: 80%;
}}

.subtitle {{

    color: #8a7a55;

    margin-top: 10px;

    font-size: 15px;
}}

.filters-sticky {{

    position: sticky;

    top: 0;

    z-index: 999;

    background:
    rgba(249,246,239,0.95);

    backdrop-filter: blur(10px);

    padding: 12px 0;

    margin-bottom: 25px;
}}

.main-filters,
.sub-filters {{

    display: flex;

    justify-content: center;

    gap: 12px;

    flex-wrap: wrap;
}}

.main-filters {{
    margin-bottom: 14px;
}}

.filter-btn {{

    padding: 10px 18px;

    border-radius: 30px;

    border: 1px solid #d8c7a2;

    background: white;

    color: #8a6b2f;

    font-weight: bold;

    cursor: pointer;
}}

.filter-btn.active {{

    background: #b9975b;

    color: white;
}}

.catalog-layout {{

    display: flex;

    gap: 24px;

    align-items: flex-start;
}}

.sidebar {{

    width: 220px;

    min-width: 220px;

    background: white;

    border-radius: 20px;

    padding: 20px;

    box-shadow:
    0 6px 18px rgba(0,0,0,0.05);

    position: sticky;

    top: 120px;

    height: fit-content;

    display: none;
}}

.sidebar.mobile-open {{
    display: block;
}}

.sidebar-title {{

    font-size: 18px;

    font-weight: bold;

    margin-bottom: 18px;

    color: #8a6b2f;
}}

.size-option {{

    display: block;

    margin-bottom: 10px;

    cursor: pointer;
}}

.size-option input {{
    margin-right: 8px;
}}

.main-content {{
    flex: 1;
}}

.grid {{

    display: grid;

    grid-template-columns:
    repeat(auto-fill, minmax(320px, 1fr));

    gap: 24px;
}}

.card {{

    background: white;

    border-radius: 22px;

    overflow: hidden;

    box-shadow:
    0 8px 20px rgba(0,0,0,0.05);
}}

.image-container {{

    width: 100%;

    height: 360px;

    background:
    linear-gradient(
        to bottom,
        #f8f6f2,
        #f1ede5
    );

    display: flex;

    align-items: flex-end;

    justify-content: center;

    padding-bottom: 20px;
}}

.image-container img {{

    width: 94%;

    height: 94%;

    object-fit: contain;
}}

.content {{
    padding: 22px;
}}

.category {{

    font-size: 13px;

    color: #8a7a55;

    margin-bottom: 12px;
}}

.title {{

    font-size: 21px;

    font-weight: bold;

    line-height: 1.35;

    min-height: 62px;

    margin-bottom: 20px;
}}

.price {{

    font-size: 36px;

    font-weight: bold;

    color: #9a6f20;

    margin-bottom: 16px;
}}

.sizes {{

    font-size: 14px;

    line-height: 1.8;
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
}}

.hidden {{
    display: none;
}}

.menu-btn {{

    border:none;

    background:white;

    border-radius:12px;

    padding:10px 14px;

    font-size:22px;

    cursor:pointer;

    box-shadow:
    0 4px 12px rgba(0,0,0,0.08);
}}

@media(max-width:768px){{

    .catalog-layout {{
        flex-direction: column;
    }}

    .sidebar {{

        width: 100%;

        min-width: 100%;

        position: relative;

        top: 0;
    }}

    .grid {{

        grid-template-columns:
        repeat(2, 1fr);

        gap: 12px;
    }}

    .image-container {{
        height: 210px;
    }}

    .title {{
        font-size: 14px;
        min-height: 42px;
    }}

    .price {{
        font-size: 22px;
    }}

    .content {{
        padding: 14px;
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

<div style="margin-bottom:16px;">

    <button
    class="menu-btn"
    onclick="toggleSidebarMenu()">

    ☰

    </button>

</div>

<div class="catalog-layout">

    <div class="sidebar"
    id="sizeSidebar">

        <div class="sidebar-title">
            FILTRAR TALLAS
        </div>

        <div id="sizeFilters"></div>

    </div>

    <div class="main-content">

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
        "\n",
        "%0A"
    )

    html += f"""

    <div class="card"

        data-genero="{genero}"

        data-categoria="{categoria_final}"

        data-price="{precio_venta_cop}"

        data-sizes="{tallas}">

        <div class="image-container">

            <img src="{imagen}">

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

# ==========================================
# SCRIPT
# ==========================================
html += """

        </div>

    </div>

</div>

<script>

let currentGender = 'all';
let currentCategory = 'Shoes';
let selectedSizes = [];

function refreshProducts(){

    const cards =
    document.querySelectorAll('.card');

    let availableSizes = [];

    cards.forEach(card => {

        const genero =
        card.dataset.genero;

        const categoria =
        card.dataset.categoria;

        const sizes =
        card.dataset.sizes || '';

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

            sizes
            .split(',')
            .forEach(size => {

                const clean = size.trim();

                if(
                    clean !== ''
                    &&
                    !availableSizes.includes(clean)
                ){
                    availableSizes.push(clean);
                }

            });
        }

    });

    buildSizeFilters(availableSizes);

    cards.forEach(card => {

        const genero =
        card.dataset.genero;

        const categoria =
        card.dataset.categoria;

        const sizes =
        (card.dataset.sizes || '')
        .split(',')
        .map(x => x.trim());

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

        if(selectedSizes.length > 0){

            const hasSize =
            selectedSizes.some(size =>
                sizes.includes(size)
            );

            if(!hasSize){
                show = false;
            }
        }

        if(show){
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }

    });
}

function buildSizeFilters(sizes){

    const container =
    document.getElementById('sizeFilters');

    container.innerHTML = '';

    const alphaSizes = [];
    const numericSizes = [];

    sizes.forEach(size => {

        const clean = size.trim();

        if(/^[0-9.]+$/.test(clean)){
            numericSizes.push(clean);
        } else {
            alphaSizes.push(clean);
        }

    });

    alphaSizes.sort((a,b) => a.localeCompare(b));
    numericSizes.sort((a,b) => parseFloat(a)-parseFloat(b));

    if(currentCategory === 'Clothing'){

        if(alphaSizes.length > 0){

            const title1 =
            document.createElement('div');

            title1.innerHTML =
            '<strong>ALFABÉRICAS</strong>';

            title1.style.marginBottom =
            '12px';

            title1.style.marginTop =
            '10px';

            container.appendChild(title1);

            alphaSizes.forEach(size => {
                appendSizeOption(container, size);
            });
        }

        if(numericSizes.length > 0){

            const title2 =
            document.createElement('div');

            title2.innerHTML =
            '<strong>NUMÉRICAS</strong>';

            title2.style.marginBottom =
            '12px';

            title2.style.marginTop =
            '18px';

            container.appendChild(title2);

            numericSizes.forEach(size => {
                appendSizeOption(container, size);
            });
        }

    } else {

        sizes.sort((a,b)=>
            a.localeCompare(b)
        );

        sizes.forEach(size => {
            appendSizeOption(container, size);
        });
    }
}

function appendSizeOption(container, size){

    const item =
    document.createElement('label');

    item.className =
    'size-option';

    item.innerHTML = `
        <input
            type="checkbox"
            value="${size}"
            onchange="toggleSize(this)">
        ${size}
    `;

    container.appendChild(item);
}

function toggleSize(checkbox){

    const value = checkbox.value;

    if(checkbox.checked){

        if(!selectedSizes.includes(value)){
            selectedSizes.push(value);
        }

    } else {

        selectedSizes =
        selectedSizes.filter(
            x => x !== value
        );
    }

    refreshProducts();
}

function toggleSidebarMenu(){

    const sidebar =
    document.getElementById('sizeSidebar');

    sidebar.classList.toggle('mobile-open');
}

function clearMainButtons(){

    document
    .querySelectorAll(
        '.main-filters .filter-btn'
    )
    .forEach(btn => {
        btn.classList.remove('active');
    });
}

function clearSubButtons(){

    document
    .querySelectorAll(
        '.sub-filters .filter-btn'
    )
    .forEach(btn => {
        btn.classList.remove('active');
    });
}

function setGender(gender, button){

    currentGender = gender;

    selectedSizes = [];

    clearMainButtons();

    button.classList.add('active');

    refreshProducts();
}

function setCategory(category, button){

    currentCategory = category;

    selectedSizes = [];

    clearSubButtons();

    button.classList.add('active');

    refreshProducts();
}

function sortProducts(order){

    const grid =
    document.getElementById(
        'productGrid'
    );

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

print("CATALOGO GENERADO")

# ==========================================
# SUBIR A GITHUB
# ==========================================
try:

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

    print("CATALOGO PUBLICADO")

except Exception as e:

    print("ERROR:", e)