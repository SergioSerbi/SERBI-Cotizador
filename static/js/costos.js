let temporizadorCostos;
let busquedaCostosActual = 0;
const dineroCostos = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
const costo$ = (selector) => document.querySelector(selector);

function formatoCosto(valor) {
    return dineroCostos.format(Number(valor || 0)).replace(".00", "");
}

function escCosto(valor) {
    const div = document.createElement("div");
    div.textContent = String(valor ?? "");
    return div.innerHTML;
}

function renderCostos(costo) {
    const entradas = Object.entries(costo || {});
    if (!entradas.length) return '<p class="costoAyuda">Sin costo cargado en esta lista.</p>';
    return entradas.map(([linea, categorias]) =>
        '<div class="costoGrupo"><p class="costoLinea">' + escCosto(linea) + '</p>' +
        Object.entries(categorias || {}).map(([categoria, valor]) =>
            '<div class="costoFila"><span>' + escCosto(categoria) +
            '</span><strong>' + formatoCosto(valor) +
            ' <span class="costoIva">+ IVA</span></strong></div>'
        ).join('') + '</div>'
    ).join('');
}

function renderPublico(publico) {
    const entradas = Object.entries(publico || {});
    if (!entradas.length) return '<p class="costoAyuda">Sin precio público relacionado en esta lista.</p>';
    return entradas.map(([linea, valor]) =>
        '<div class="costoFila"><span>' + escCosto(linea) +
        '</span><strong>' + formatoCosto(valor) +
        ' <span class="costoIva">IVA incluido</span></strong></div>'
    ).join('');
}

function cardCosto(p) {
    const lineas = (p.lineas || []).map(escCosto).join(' · ') || 'Línea no indicada';
    const presentacion = p.presentacion
        ? ' · <strong>Presentación: ' + escCosto(p.presentacion) + '</strong>'
        : '';
    const fuente = [...(p.fuentes_costos || []), ...(p.fuentes_publico || [])]
        .slice(0, 2).map(escCosto).join(' · ');

    return '<article class="costoCard">' +
        '<div class="costoCab"><div><div class="costoCodigo">' + escCosto(p.codigo) +
        ' <span class="costoBase">Base ' + escCosto(p.codigo_base) + '</span></div>' +
        '<h2>' + escCosto(p.descripcion) + '</h2>' +
        '<p class="costoMeta">' + lineas + presentacion + '</p></div>' +
        '<span class="costoBadge">SAYER</span></div>' +
        '<div class="costosBloques">' +
        '<section class="costoBloque costo"><h3>COSTO SAYER — MÁS IVA</h3>' +
        renderCostos(p.costos_por_linea) + '</section>' +
        '<section class="costoBloque publico"><h3>PRECIO PÚBLICO — IVA INCLUIDO</h3>' +
        renderPublico(p.publico_por_linea) + '</section></div>' +
        '<div class="costoFecha"><span>LISTA SAYER: ' +
        escCosto(p.fecha_lista_display || '') + '</span><span>Fuente: ' + fuente +
        '</span></div></article>';
}

function programarBusquedaCostos() {
    clearTimeout(temporizadorCostos);
    const q = costo$("#buscarCostos").value.trim();
    costo$("#limpiarCostos").hidden = !q;
    if (q.length < 2) {
        costo$("#resultadosCostos").replaceChildren();
        costo$("#ayudaCostos").textContent = "Escribe al menos 2 caracteres para buscar.";
        return;
    }
    costo$("#ayudaCostos").textContent = "Buscando en SAYER…";
    temporizadorCostos = setTimeout(buscarCostos, 180);
}

async function buscarCostos() {
    const q = costo$("#buscarCostos").value.trim();
    const id = ++busquedaCostosActual;
    try {
        const r = await fetch("/api/costos?texto=" + encodeURIComponent(q));
        if (!r.ok) throw new Error();
        const productos = await r.json();
        if (id !== busquedaCostosActual) return;
        const box = costo$("#resultadosCostos");
        box.innerHTML = productos.length
            ? productos.map(cardCosto).join("")
            : '<div class="costoVacio">No se encontraron productos con esa búsqueda.</div>';
        costo$("#ayudaCostos").textContent = productos.length
            ? productos.length + " resultado" + (productos.length === 1 ? "" : "s") + "."
            : "No se encontraron productos.";
    } catch (_) {
        if (id === busquedaCostosActual) {
            costo$("#resultadosCostos").innerHTML =
                '<div class="costoVacio">No fue posible realizar la búsqueda. Intenta de nuevo.</div>';
            costo$("#ayudaCostos").textContent = "";
        }
    }
}

function limpiarCostos() {
    busquedaCostosActual++;
    costo$("#buscarCostos").value = "";
    costo$("#limpiarCostos").hidden = true;
    costo$("#resultadosCostos").replaceChildren();
    costo$("#ayudaCostos").textContent = "Escribe al menos 2 caracteres para buscar.";
    costo$("#buscarCostos").focus();
}

window.addEventListener("DOMContentLoaded", () => {
    costo$("#buscarCostos")?.addEventListener("input", programarBusquedaCostos);
    costo$("#limpiarCostos")?.addEventListener("click", limpiarCostos);
    costo$("#buscarCostos")?.focus();
});
