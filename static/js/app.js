// ===========================
// SERBI COTIZADOR V2.2
// ===========================

let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
let productoPendiente = null;

const dinero = new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN"
});

window.addEventListener("DOMContentLoaded", () => {
    dibujarCarrito();
    configurarModal();
    configurarBuscador();
    configurarAcciones();
});

function guardarCarrito() {
    localStorage.setItem("carrito", JSON.stringify(carrito));
}

function configurarModal() {
    document.getElementById("menos").addEventListener("click", () => cambiarCantidad(-1));
    document.getElementById("mas").addEventListener("click", () => cambiarCantidad(1));
    document.getElementById("cerrarModal").addEventListener("click", cerrarModal);
    document.getElementById("cancelarModal").addEventListener("click", cerrarModal);
    document.getElementById("agregarModal").addEventListener("click", confirmarProducto);
    document.getElementById("modalProducto").addEventListener("click", (evento) => {
        if (evento.target.id === "modalProducto") cerrarModal();
    });
    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") cerrarModal();
    });
}

function configurarBuscador() {
    const txtBuscar = document.getElementById("buscar");
    txtBuscar.addEventListener("input", buscarV2);
}

function configurarAcciones() {
    document.getElementById("btnCopiar").addEventListener("click", copiarCotizacion);
    document.getElementById("btnWhatsapp").addEventListener("click", enviarWhatsApp);
    document.getElementById("btnVaciar").addEventListener("click", vaciarCarrito);
}

function abrirModal(producto) {
    productoPendiente = producto;
    const preciosDisponibles = producto.precios.filter((precio) => precio.valor > 0);
    const opcionesPrecio = document.getElementById("opcionesPrecio");
    const seccionPrecio = document.getElementById("seccionPrecio");

    document.getElementById("modalTitulo").textContent = producto.descripcion;
    document.getElementById("cantidadModal").value = 1;
    opcionesPrecio.replaceChildren();

    // Cuando solo hay un precio válido, se elige automáticamente.
    seccionPrecio.hidden = preciosDisponibles.length <= 1;
    preciosDisponibles.forEach((precio, indice) => {
        const etiqueta = document.createElement("label");
        etiqueta.className = "opcionPrecio";
        const radio = document.createElement("input");
        radio.type = "radio";
        radio.name = "precioModal";
        radio.value = precio.valor;
        radio.checked = indice === 0;
        etiqueta.append(radio, document.createTextNode(` ${precio.nombre} `));
        const importe = document.createElement("strong");
        importe.textContent = dinero.format(precio.valor);
        etiqueta.append(importe);
        opcionesPrecio.append(etiqueta);
    });

    document.getElementById("modalProducto").classList.add("activo");
    document.getElementById("cantidadModal").focus();
}

function cerrarModal() {
    document.getElementById("modalProducto")?.classList.remove("activo");
    productoPendiente = null;
}

function cambiarCantidad(cambio) {
    const campo = document.getElementById("cantidadModal");
    const actual = Math.max(1, Number.parseInt(campo.value, 10) || 1);
    campo.value = Math.max(1, actual + cambio);
}

function confirmarProducto() {
    if (!productoPendiente) return;

    const cantidad = Math.max(1, Number.parseInt(document.getElementById("cantidadModal").value, 10) || 1);
    const precioSeleccionado = document.querySelector('input[name="precioModal"]:checked');
    if (!precioSeleccionado) return;

    const precio = Number(precioSeleccionado.value);
    const existente = carrito.find((item) => item.clave === productoPendiente.clave && item.precio === precio);

    if (existente) {
        existente.cantidad += cantidad;
    } else {
        carrito.push({
            clave: productoPendiente.clave,
            descripcion: productoPendiente.descripcion,
            precio,
            cantidad
        });
    }

    cerrarModal();
    guardarCarrito();
    dibujarCarrito();
}

function dibujarCarrito() {
    const contenedor = document.getElementById("cotizacion");
    const total = carrito.reduce((acumulado, producto) => acumulado + producto.precio * producto.cantidad, 0);
    document.getElementById("total").textContent = `TOTAL: ${dinero.format(total)}`;

    if (carrito.length === 0) {
        contenedor.innerHTML = '<p class="carritoVacio">Aún no hay productos en la cotización.</p>';
        return;
    }

    contenedor.replaceChildren();
    carrito.forEach((producto, indice) => {
        const item = document.createElement("article");
        item.className = "itemCotizacion";
        item.innerHTML = `
            <div class="detalleItem">
                <h3></h3>
                <p>Clave: <span></span></p>
                <p>Precio unitario: <strong>${dinero.format(producto.precio)}</strong></p>
            </div>
            <div class="controlesItem">
                <div class="controlCantidad" aria-label="Cantidad">
                    <button type="button" aria-label="Restar">−</button>
                    <strong>${producto.cantidad}</strong>
                    <button type="button" aria-label="Sumar">+</button>
                </div>
                <strong class="importeItem">${dinero.format(producto.precio * producto.cantidad)}</strong>
                <button type="button" class="btnEliminar">Eliminar</button>
            </div>`;
        item.querySelector("h3").textContent = producto.descripcion;
        item.querySelector("span").textContent = producto.clave;
        const botonesCantidad = item.querySelectorAll(".controlCantidad button");
        botonesCantidad[0].addEventListener("click", () => restar(indice));
        botonesCantidad[1].addEventListener("click", () => sumar(indice));
        item.querySelector(".btnEliminar").addEventListener("click", () => eliminar(indice));
        contenedor.append(item);
    });
}

function sumar(indice) {
    carrito[indice].cantidad += 1;
    guardarCarrito();
    dibujarCarrito();
}

function restar(indice) {
    if (carrito[indice].cantidad <= 1) carrito.splice(indice, 1);
    else carrito[indice].cantidad -= 1;
    guardarCarrito();
    dibujarCarrito();
}

function eliminar(indice) {
    carrito.splice(indice, 1);
    guardarCarrito();
    dibujarCarrito();
}

function vaciarCarrito() {
    if (!carrito.length) return;
    carrito = [];
    guardarCarrito();
    dibujarCarrito();
}

async function buscarV2() {
    const texto = document.getElementById("buscar").value.trim();
    const resultados = document.getElementById("resultados");
    if (texto.length < 2) {
        resultados.replaceChildren();
        return;
    }

    try {
        const respuesta = await fetch(`/buscar?texto=${encodeURIComponent(texto)}`);
        if (!respuesta.ok) throw new Error("No fue posible buscar productos.");
        const productos = await respuesta.json();
        resultados.replaceChildren();
        productos.filter((p) => Number(p["PRECIO 1"]) > 0).forEach((p) => {
            const tarjeta = document.createElement("article");
            tarjeta.className = "producto";
            const descripcion = document.createElement("div");
            descripcion.className = "descripcionProducto";
            descripcion.textContent = p.DESCRIPCION;
            const boton = document.createElement("button");
            boton.className = "btnAgregar";
            boton.type = "button";
            boton.textContent = "Agregar";
            boton.addEventListener("click", () => abrirModal({
                clave: String(p.CLAVE || ""),
                descripcion: String(p.DESCRIPCION || "Sin descripción"),
                precios: [
                    { nombre: "Precio 1", valor: Number(p["PRECIO 1"]) },
                    { nombre: "Precio 2", valor: Number(p["PRECIO 2"]) },
                    { nombre: "Precio 3", valor: Number(p["PRECIO 3"]) }
                ]
            }));
            tarjeta.append(descripcion, boton);
            resultados.append(tarjeta);
        });
        if (!resultados.children.length) resultados.innerHTML = '<p class="sinResultados">No se encontraron productos con precio disponible.</p>';
    } catch (error) {
        resultados.innerHTML = '<p class="sinResultados">No fue posible realizar la búsqueda. Intenta de nuevo.</p>';
    }
}

function textoCotizacion() {
    let total = 0;
    const lineas = carrito.map((producto, indice) => {
        const importe = producto.precio * producto.cantidad;
        total += importe;
        return `${indice + 1}. ${producto.descripcion}\nClave: ${producto.clave}\nCantidad: ${producto.cantidad}\nPrecio: ${dinero.format(producto.precio)}\nImporte: ${dinero.format(importe)}`;
    });
    return `COTIZACIÓN SERBI\n\n${lineas.join("\n\n")}\n\n--------------------------\nTOTAL: ${dinero.format(total)}`;
}

async function copiarCotizacion() {
    if (!carrito.length) return alert("No hay productos en la cotización.");
    try {
        await navigator.clipboard.writeText(textoCotizacion());
        alert("Cotización copiada al portapapeles.");
    } catch (_) {
        alert("No fue posible copiar la cotización.");
    }
}

function enviarWhatsApp() {
    if (!carrito.length) return alert("No hay productos en la cotización.");
    window.open(`https://wa.me/?text=${encodeURIComponent(textoCotizacion())}`, "_blank", "noopener");
}
