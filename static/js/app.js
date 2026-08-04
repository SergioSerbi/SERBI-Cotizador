// SERBI Cotizador v3.0
let carrito = JSON.parse(localStorage.getItem("serbi-carrito-v3")) || [];
let productoPendiente = null;
let temporizadorBusqueda;
let busquedaActual = 0;
let ultimoEnfoque = null;

const dinero = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
const $ = (selector) => document.querySelector(selector);

window.addEventListener("DOMContentLoaded", () => {
    dibujarCarrito();
    configurarEventos();
    $("#buscar").focus();
});

function configurarEventos() {
    $("#buscar").addEventListener("input", programarBusqueda);
    $("#limpiarBusqueda").addEventListener("click", limpiarBusqueda);
    $("#abrirCarrito").addEventListener("click", abrirCarrito);
    $("#cerrarCarrito").addEventListener("click", cerrarCarrito);
    $("#fondoCarrito").addEventListener("click", cerrarCarrito);
    $("#btnCopiar").addEventListener("click", copiarCotizacion);
    $("#btnWhatsapp").addEventListener("click", enviarWhatsApp);
    $("#btnVaciar").addEventListener("click", pedirVaciado);
    $("#confirmarVaciado").addEventListener("click", vaciarCarrito);
    $("#cancelarVaciado").addEventListener("click", () => cerrarModal("#modalConfirmacion"));
    $("#menos").addEventListener("click", () => cambiarCantidad(-1));
    $("#mas").addEventListener("click", () => cambiarCantidad(1));
    $("#cerrarModal").addEventListener("click", cerrarProducto);
    $("#cancelarModal").addEventListener("click", cerrarProducto);
    $("#agregarModal").addEventListener("click", confirmarProducto);
    document.querySelectorAll(".modal").forEach((modal) => modal.addEventListener("click", (e) => {
        if (e.target === modal) cerrarModal(`#${modal.id}`);
    }));
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") { cerrarProducto(); cerrarModal("#modalConfirmacion"); cerrarCarrito(); }
    });
}

function guardarCarrito() { localStorage.setItem("serbi-carrito-v3", JSON.stringify(carrito)); }

function programarBusqueda() {
    clearTimeout(temporizadorBusqueda);
    const texto = $("#buscar").value.trim();
    $("#limpiarBusqueda").hidden = !texto;
    if (texto.length < 2) {
        $("#resultados").replaceChildren();
        $("#ayudaBusqueda").textContent = "Escribe al menos 2 caracteres para buscar.";
        return;
    }
    $("#ayudaBusqueda").textContent = "Buscando productos…";
    temporizadorBusqueda = setTimeout(buscarProductos, 250);
}

async function buscarProductos() {
    const texto = $("#buscar").value.trim();
    const id = ++busquedaActual;
    try {
        const respuesta = await fetch(`/buscar?texto=${encodeURIComponent(texto)}`);
        if (!respuesta.ok) throw new Error("Error al buscar");
        const productos = await respuesta.json();
        if (id !== busquedaActual) return;
        mostrarResultados(productos);
    } catch (_) {
        if (id === busquedaActual) {
            $("#resultados").innerHTML = '<p class="mensajeResultados">No fue posible realizar la búsqueda. Intenta de nuevo.</p>';
            $("#ayudaBusqueda").textContent = "";
        }
    }
}

function mostrarResultados(productos) {
    const resultados = $("#resultados");
    resultados.replaceChildren();
    const disponibles = productos.filter((p) => preciosDe(p).length);
    $("#ayudaBusqueda").textContent = disponibles.length ? `${disponibles.length} producto${disponibles.length === 1 ? "" : "s"} encontrado${disponibles.length === 1 ? "" : "s"}.` : "";
    if (!disponibles.length) {
        resultados.innerHTML = '<p class="mensajeResultados">No se encontraron productos con precio disponible.</p>';
        return;
    }
    disponibles.forEach((producto) => {
        const tarjeta = document.createElement("article");
        tarjeta.className = "producto";
        tarjeta.innerHTML = '<div><p class="claveProducto"></p><h2></h2><p class="precioDesde"></p></div><button class="btnAgregar" type="button">Agregar <span aria-hidden="true">+</span></button>';
        tarjeta.querySelector(".claveProducto").textContent = `Clave: ${producto.CLAVE || "—"}`;
        tarjeta.querySelector("h2").textContent = producto.DESCRIPCION || "Sin descripción";
        const precios = preciosDe(producto);
        tarjeta.querySelector(".precioDesde").textContent = precios.length === 1 ? dinero.format(precios[0].valor) : `Desde ${dinero.format(Math.min(...precios.map(p => p.valor)))}`;
        tarjeta.querySelector("button").addEventListener("click", () => abrirModal(producto));
        resultados.append(tarjeta);
    });
}

function preciosDe(producto) {
    return [1, 2, 3].map((numero) => ({ nombre: `Precio ${numero}`, valor: Number(producto[`PRECIO ${numero}`]) }))
        .filter((precio) => Number.isFinite(precio.valor) && precio.valor > 0);
}

function abrirModal(producto) {
    ultimoEnfoque = document.activeElement;
    productoPendiente = { clave: String(producto.CLAVE || ""), descripcion: String(producto.DESCRIPCION || "Sin descripción"), precios: preciosDe(producto) };
    $("#modalTitulo").textContent = productoPendiente.descripcion;
    $("#modalClave").textContent = productoPendiente.clave ? `Clave: ${productoPendiente.clave}` : "";
    $("#cantidadModal").value = 1;
    const opciones = $("#opcionesPrecio");
    opciones.replaceChildren();
    $("#seccionPrecio").hidden = productoPendiente.precios.length === 1;
    productoPendiente.precios.forEach((precio, indice) => {
        const opcion = document.createElement("label");
        opcion.className = "opcionPrecio";
        opcion.innerHTML = `<input type="radio" name="precioModal" value="${precio.valor}" ${indice === 0 ? "checked" : ""}><span>${precio.nombre}</span><strong>${dinero.format(precio.valor)}</strong>`;
        opciones.append(opcion);
    });
    abrirModalBase("#modalProducto", "#cantidadModal");
}

function confirmarProducto() {
    if (!productoPendiente) return;
    const cantidad = Math.min(9999, Math.max(1, Number.parseInt($("#cantidadModal").value, 10) || 1));
    const elegido = document.querySelector('input[name="precioModal"]:checked');
    const precio = Number(elegido?.value ?? productoPendiente.precios[0]?.valor);
    if (!precio) return;
    const existente = carrito.find((item) => item.clave === productoPendiente.clave && item.precio === precio);
    if (existente) existente.cantidad += cantidad;
    else carrito.push({ clave: productoPendiente.clave, descripcion: productoPendiente.descripcion, precio, cantidad });
    const mensaje = existente ? `Se sumaron ${cantidad} unidad${cantidad === 1 ? "" : "es"} al producto existente.` : "Producto agregado a la cotización.";
    cerrarProducto(); guardarCarrito(); dibujarCarrito(); limpiarBusqueda(); mostrarToast(mensaje);
}

function cambiarCantidad(cambio) {
    const campo = $("#cantidadModal");
    campo.value = Math.min(9999, Math.max(1, (Number.parseInt(campo.value, 10) || 1) + cambio));
}

function cerrarProducto() { cerrarModal("#modalProducto"); productoPendiente = null; }
function abrirModalBase(selector, foco) { const modal = $(selector); modal.hidden = false; requestAnimationFrame(() => { modal.classList.add("activo"); $(foco)?.focus(); }); }
function cerrarModal(selector) { const modal = $(selector); if (!modal || modal.hidden) return; modal.classList.remove("activo"); setTimeout(() => { modal.hidden = true; }, 180); ultimoEnfoque?.focus?.(); }

function dibujarCarrito() {
    const contenedor = $("#cotizacion");
    const piezas = carrito.reduce((suma, item) => suma + item.cantidad, 0);
    const total = carrito.reduce((suma, item) => suma + item.precio * item.cantidad, 0);
    $("#total").textContent = dinero.format(total);
    $("#contadorCarrito").textContent = piezas;
    $("#contadorPanel").textContent = piezas;
    $("#btnVaciar").hidden = !carrito.length;
    if (!carrito.length) { contenedor.innerHTML = '<div class="carritoVacio"><span>🛒</span><p>Tu cotización está vacía.</p><small>Agrega productos desde el buscador.</small></div>'; return; }
    contenedor.replaceChildren();
    carrito.forEach((producto, indice) => {
        const item = document.createElement("article"); item.className = "itemCotizacion";
        item.innerHTML = `<div class="detalleItem"><h3></h3><p></p><strong>${dinero.format(producto.precio)}</strong></div><div class="controlesItem"><button class="btnQuitar" type="button" aria-label="Eliminar producto">×</button><div class="controlCantidad"><button type="button" aria-label="Restar">−</button><span>${producto.cantidad}</span><button type="button" aria-label="Sumar">+</button></div><strong class="importeItem">${dinero.format(producto.precio * producto.cantidad)}</strong></div>`;
        item.querySelector("h3").textContent = producto.descripcion;
        item.querySelector("p").textContent = producto.clave ? `Clave: ${producto.clave}` : "";
        const botones = item.querySelectorAll(".controlCantidad button");
        botones[0].addEventListener("click", () => ajustarCantidad(indice, -1)); botones[1].addEventListener("click", () => ajustarCantidad(indice, 1));
        item.querySelector(".btnQuitar").addEventListener("click", () => { carrito.splice(indice, 1); guardarCarrito(); dibujarCarrito(); }); contenedor.append(item);
    });
}

function ajustarCantidad(indice, cambio) { carrito[indice].cantidad += cambio; if (carrito[indice].cantidad < 1) carrito.splice(indice, 1); guardarCarrito(); dibujarCarrito(); }
function abrirCarrito() { $("#panelCarrito").classList.add("abierto"); $("#fondoCarrito").hidden = false; $("#abrirCarrito").setAttribute("aria-expanded", "true"); $("#panelCarrito").setAttribute("aria-hidden", "false"); }
function cerrarCarrito() { $("#panelCarrito").classList.remove("abierto"); $("#fondoCarrito").hidden = true; $("#abrirCarrito").setAttribute("aria-expanded", "false"); $("#panelCarrito").setAttribute("aria-hidden", "true"); }
function pedirVaciado() { if (carrito.length) abrirModalBase("#modalConfirmacion", "#cancelarVaciado"); }
function vaciarCarrito() { carrito = []; guardarCarrito(); dibujarCarrito(); cerrarModal("#modalConfirmacion"); mostrarToast("La cotización quedó vacía."); }
function limpiarBusqueda() { busquedaActual++; $("#buscar").value = ""; $("#limpiarBusqueda").hidden = true; $("#resultados").replaceChildren(); $("#ayudaBusqueda").textContent = "Escribe al menos 2 caracteres para buscar."; $("#buscar").focus(); }

function textoCotizacion() { let total = 0; const lineas = carrito.map((p, i) => { const importe = p.precio * p.cantidad; total += importe; return `${i + 1}. ${p.descripcion}\n   Clave: ${p.clave || "—"}\n   ${p.cantidad} × ${dinero.format(p.precio)} = ${dinero.format(importe)}`; }); return `COTIZACIÓN SERBI\n\n${lineas.join("\n\n")}\n\nTOTAL: ${dinero.format(total)}`; }
async function copiarCotizacion() { if (!carrito.length) return mostrarToast("Agrega productos antes de copiar.", true); try { await navigator.clipboard.writeText(textoCotizacion()); mostrarToast("Cotización copiada al portapapeles."); } catch (_) { mostrarToast("No fue posible copiar la cotización.", true); } }
function enviarWhatsApp() { if (!carrito.length) return mostrarToast("Agrega productos antes de enviarla.", true); window.open(`https://wa.me/?text=${encodeURIComponent(textoCotizacion())}`, "_blank", "noopener,noreferrer"); }
function mostrarToast(mensaje, esError = false) { const toast = $("#toast"); toast.textContent = mensaje; toast.classList.toggle("error", esError); toast.hidden = false; requestAnimationFrame(() => toast.classList.add("visible")); clearTimeout(mostrarToast.id); mostrarToast.id = setTimeout(() => { toast.classList.remove("visible"); setTimeout(() => { toast.hidden = true; }, 180); }, 3000); }
