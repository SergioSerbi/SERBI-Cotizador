// ===========================
// SERBI COTIZADOR V2
// ===========================

let carrito = JSON.parse(localStorage.getItem("carrito")) || [];

window.onload = () => {
    dibujarCarrito();
};

function guardarCarrito() {
    localStorage.setItem("carrito", JSON.stringify(carrito));
}

function agregarProducto(clave, descripcion, precio1, precio2, precio3) {

    let opcion = prompt(
`¿Qué precio deseas usar?

1 = $${precio1.toFixed(2)}
2 = $${precio2.toFixed(2)}
3 = $${precio3.toFixed(2)}`, "1");

    if (opcion === null) return;

    let precio = Number(precio1);

    if (opcion == "2") precio = Number(precio2);
    if (opcion == "3") precio = Number(precio3);

    let cantidad = prompt("Cantidad", "1");

    if (cantidad === null) return;

    cantidad = parseInt(cantidad);

    if (isNaN(cantidad) || cantidad <= 0) {
        cantidad = 1;
    }

    carrito.push({
        clave: clave,
        descripcion: descripcion,
        precio: precio,
        cantidad: cantidad
    });

    guardarCarrito();
    dibujarCarrito();
}

function dibujarCarrito() {

    const contenedor = document.getElementById("cotizacion");

    let html = "";
    let total = 0;

    carrito.forEach((p, index) => {

        let importe = p.precio * p.cantidad;
        total += importe;

        html += `
        <div class="itemCotizacion">

            <h3>${p.descripcion}</h3>

            <b>Clave:</b> ${p.clave}<br><br>

            <button onclick="restar(${index})">-</button>

            <b style="margin:15px">${p.cantidad}</b>

            <button onclick="sumar(${index})">+</button>

            <br><br>

            Precio:
            <b>$${p.precio.toFixed(2)}</b>

            <br>

            Importe:
            <b>$${importe.toFixed(2)}</b>

            <br><br>

            <button onclick="eliminar(${index})">
                🗑 Eliminar
            </button>

            <hr>

        </div>
        `;
    });

    contenedor.innerHTML = html;

    document.getElementById("total").innerHTML =
        "TOTAL: $" + total.toFixed(2);
}

function sumar(i) {
    carrito[i].cantidad++;
    guardarCarrito();
    dibujarCarrito();
}

function restar(i) {
    carrito[i].cantidad--;

    if (carrito[i].cantidad <= 0) {
        carrito.splice(i, 1);
    }

    guardarCarrito();
    dibujarCarrito();
}

function eliminar(i) {
    carrito.splice(i, 1);
    guardarCarrito();
    dibujarCarrito();
}

function vaciarCarrito() {
    carrito = [];
    guardarCarrito();
    dibujarCarrito();
}

// ===========================
// BUSCADOR
// ===========================

const txtBuscar = document.getElementById("buscar");

if (txtBuscar) {
    txtBuscar.addEventListener("keyup", buscarV2);
}

async function buscarV2() {

    const texto = txtBuscar.value.trim();

    if (texto.length < 2) {
        document.getElementById("resultados").innerHTML = "";
        return;
    }

    const respuesta = await fetch("/buscar?texto=" + encodeURIComponent(texto));
    const productos = await respuesta.json();

    let html = "";

    productos.forEach(p => {

    const precio1 = Number(p["PRECIO 1"]);

    if (precio1 <= 0) return;

    html += `
    <div class="producto">

        <div class="infoProducto">

            <div class="descripcionProducto">
                ${p.DESCRIPCION}
            </div>

        </div>

        <button class="btnAgregar" onclick="agregarProducto(
            '${p.CLAVE}',
            '${String(p.DESCRIPCION).replace(/'/g,"\\'")}',
            ${Number(p["PRECIO 1"])},
            ${Number(p["PRECIO 2"])},
            ${Number(p["PRECIO 3"])}
        )">
            ➕ Agregar
        </button>

    </div>
    `;

});

    document.getElementById("resultados").innerHTML = html;
}
// ===========================
// COPIAR COTIZACIÓN
// ===========================

const btnCopiar = document.getElementById("btnCopiar");

if (btnCopiar) {

    btnCopiar.addEventListener("click", () => {

        if (carrito.length === 0) {
            alert("No hay productos en la cotización.");
            return;
        }

        let texto = "🧾 COTIZACIÓN SERBI\n\n";
        let total = 0;

        carrito.forEach((p, i) => {

            const importe = p.precio * p.cantidad;
            total += importe;

            texto += `${i + 1}. ${p.descripcion}
Cantidad: ${p.cantidad}
Precio: $${p.precio.toFixed(2)}
Importe: $${importe.toFixed(2)}

`;
        });

        texto += "--------------------------\n";
        texto += "TOTAL: $" + total.toFixed(2);

        navigator.clipboard.writeText(texto)
            .then(() => alert("Cotización copiada al portapapeles"))
            .catch(() => alert("No fue posible copiar la cotización"));

    });

}