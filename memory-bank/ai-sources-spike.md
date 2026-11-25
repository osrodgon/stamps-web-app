# A0 — Prueba de fuentes (2026-11-25)

Resultado de ejecutar `manage.py ai_sources_probe` contra las cuatro fuentes
previstas en `ai-api-plan.md` §2 y §4. Este documento existe para que el usuario
valide los datos antes de escribir ningún adaptador (A2–A7).

- Comando: `python manage.py ai_sources_probe` (repetible; `--source delcampe`
  para una sola, `--delay` para separar peticiones, `--json` para otra ruta).
- Cliente: `requests`/urllib3, HTTP/1.1, User-Agent
  `stamps-web-app-probe/0.1 (+https://github.com/oscarro/stamps-web-app)`,
  5 s entre peticiones al mismo host.
- Evidencia cruda: `memory-bank/ai-sources-spike.json` (sin cuerpos de respuesta,
  sólo código, tiempos, forma y lo que extrajo cada parser).
- Cinco series reales de la base de producción (2026-11-25), elegidas para cubrir
  el catálogo: una clásica (1850), dos de 1928–1930, la más larga (57 sellos,
  1992) y una moderna (1998).

| # | id | Serie | Año | Sellos | 1.er Edifil | 1.er Fesofi |
|---|----|-------|-----|--------|-------------|-------------|
| 1 | 2551 | Isabel II | 1850 | 5 | 1 | 0001 |
| 2 | 71 | Pro Catacumbas de San Dámaso | 1928 | 32 | 402 | 0402 |
| 3 | 81 | Quinta de Goya en la Exposición de Sevilla | 1930 | 14 | 517 | 0517 |
| 4 | 842 | Expo 92 Sevilla | 1992 | 57 | 3164 | 3196 |
| 5 | 1010 | Correspondencia epistolar escolar | 1998 | 27 | 3560 | 1998026 |

## Resumen

| Fuente | Alcanzable | robots.txt | ¿Sirve? | Veredicto |
|--------|-----------|------------|---------|-----------|
| Colnect (API CAPI) | sí (401 sin clave) | `Crawl-delay: 10` | sí, es la única puerta | **necesita la clave**; el sitio público está tras Anubis |
| Delcampe | sí | **prohíbe la búsqueda** | los datos están, el permiso no | **descartar scraping** |
| Iberphil | sí | sin reglas | martillo sólo a veces, sin código | fuente débil, fuera de la 1.ª versión |
| Fesofi (no estaba en el plan) | sí | sin reglas | **sí, y mucho** | API pública exacta: código Fesofi → Edifil + ficha |

## Colnect

- `robots.txt` → 200 (11.614 B). Grupo `*`: `Crawl-delay: 10`,
  `/en/stamps/list/` permitido.
- `https://api.colnect.net/en/api/000000/categories` con HTTP/1.1 → **426**
  `{"error":"HTTP/2 required","message":"This endpoint requires HTTP/2…"}`.
- La misma URL con HTTP/2 (`curl`, negociación por defecto) → **401**
  `{"error":"Invalid appId!"}`. Es decir: **la red llega a la CAPI**, lo único
  que falta es la clave. No es un problema de firewall ni de host.
- `httpx` 0.28.1 está instalado en el contenedor pero **sin el paquete `h2`**:
  `httpx.Client(http2=True)` lanza `ImportError` ("pip install httpx[http2]").
  A2 tiene que declarar `httpx[http2]`, no `httpx` a secas.
- Sitio público (`colnect.com/en/stamps/list/country/67-Spain/year/1850`) → 200
  pero es la página de **Anubis** («Colnect Collectors Protection»), 4.886 B,
  igual en tres URLs distintas. **Scrapear el catálogo público no es una opción**;
  la CAPI es la única puerta.

## Delcampe

- `https://www.delcampe.net/robots.txt` → 200 (14.316 B). En el grupo `*`, una
  línea por idioma: **`Disallow: /en_GB/collectables/search`** (y `/es/…`,
  `/fr/…`, `/de/…`, `/it/…`, `/nl/…`). Es exactamente la URL que necesita un
  buscador por código.
- La búsqueda **funciona**: el formulario usa `term=`, no `q=` (con `q` Delcampe
  ignora el texto y sirve la portada de coleccionables — así se leyó mal en la
  primera pasada: 5 tarjetas irrelevantes). Con `term=`:

| Consulta | Tarjetas | Con «edifil» en el título | Ejemplo real |
|----------|----------|---------------------------|--------------|
| `1 1850` | 5 | 0 | «PRUSSIA 1850s 1 Silbergroschen…» (no es nuestro sello) |
| `402 1928` | 5 | 1 | «1928- ED. 402, 403 y 404 PRO CATACUMBAS DE SAN DÁMASO…» €0,80 |
| `517 1930` | 5 | 0 | devuelve Austria/Michel 512-517, no Edifil |
| `3164 1992` | 5 | 2 | «Spain 1992. Expo Sevilla'92. Ed 3164-87 (**)» €3,50 |
| `3560 1998` | 5 | 1 | «1998-ED. 3560 a 3583-M.P.61A-B-EL QUIJOTE por MINGOTE» €5,25 |

  Es decir: cuando el código está en el título, el resultado es el bueno; cuando
  no, hay que descartar a mano. La señal existe.
- **Decisión propuesta: descartar Delcampe por scraping.** `robots.txt` lo
  prohíbe en la ruta necesaria, y A4 era precisamente el paso condicionado a
  esta prueba. Alternativas: agregador de pago (ReefAPI y similares) o dejarlo
  fuera. No se implementa nada en A4 hasta que se decida.

## Iberphil

- `robots.txt` → 200 (457 B), sin regla para `/es/subastas`; no hay buscador en
  el sitio (`search_available: false`).
- El histórico lista las subastas; `…/auction-sold-lots` es una tabla de **tres
  columnas**: `N° Lote`, `Clasificación`, **`Puja inicial (€)`**. No hay precio
  de adjudicación.
- El martillo está en la ficha del lote, y **sólo a veces**. Comprobado a mano:
  la subasta 46 (cerrada) sí lo muestra — `Adjudicación 90€`, `15€`, `5€` y `0€`
  para los no vendidos; en la 47 (la más reciente) y en la 1 (la más antigua)
  las fichas muestreadas **no tienen bloque de adjudicación**. El comando
  registra `hammers: [null, null, null, null]` sobre la 47.
- Ninguna ficha menciona Edifil ni Fesofi (`mentions_edifil: false` en todas):
  el emparejamiento sería por texto libre, lote a lote, una petición por lote.
- **Veredicto: fuente débil.** Sirve para clásicos y series completas, no para
  un sello suelto, y no se puede unir por código. Fuera de la primera versión de
  A7; si entra, como `auction_hammer` con `subject` a nivel de serie y
  `raw` guardando la ficha.

## Fesofi — el hallazgo de A0

No estaba en el plan. Las páginas HTML del catálogo se pintan con JavaScript
(0 productos en el HTML de una categoría), pero el sitio es WooCommerce y expone
la **Store API pública, sin clave**:

```
GET https://catalogodesellos.fesofi.es/wp-json/wc/store/v1/products?sku=<código>
```

- `sku` es **exacto**: `sku=999999999` → `[]`; `sku=3196` → un solo producto.
- El producto trae, como atributos: `Número EDIFIL`, `Título Serie`,
  `Número Fesofi`, `Año de Emisión`, `Fecha De Emisión`, `Facial`, `Color`,
  `Dentado`, `Impresión`, `Imprenta`, `Tirada`, `Tipo De Correo`,
  `Valores De La Serie`, `Motivo Sello`.
- Los precios son `0`: es un catálogo descriptivo, **no una fuente de valoración**.

Resultado sobre las cinco series (buscando por el código Fesofi del primer sello):

| Código Fesofi | Producto | EDIFIL devuelto | Título de serie | Facial | Tirada |
|---------------|----------|-----------------|-----------------|--------|--------|
| 0001 | 0001 | 1 | Isabel II | 6 cuartos | 6.226.727 |
| 0402 | 0402 | 402 | Pro Catacumbas de San Dámaso | 2 cts | 67.700 |
| 0517 | 0517 | 517 | Quinta de Goya en la E de Sevilla (abreviado) | 5 cts | 474.000 |
| 3196 | 3196 | 3188 | Expo 92 Sevilla | 17 + 5 pta | 25.920.000 |
| 1998026 | 3601SPD | — | — (ese código no es un `sku`; devuelve el sobre del PDD) | — | — |

Cuatro de cinco resuelven con ficha completa; el quinto (una serie de 1998 con
código Fesofi largo) no está indexado por `sku`.

**Consecuencia para el plan:** Fesofi es el puente de identidad que A6 necesitaba
—código Fesofi → código Edifil, título de serie, facial, tirada, color, dentado,
imprenta— sin clave, sin coste y con JSON. Reduce lo que el LLM tiene que
«saber» y da una segunda fuente de hechos de catálogo además de Colnect.

### Aviso de datos para A6

`min(edifil)` y `min(fesofi)` de una serie **no son el mismo sello**. En Expo 92,
Fesofi 3196 ↔ Edifil 3188 (comprobado en la base: `stamps_api_stamp` id 3333),
mientras que el Edifil mínimo de la serie es 3164 (otro sello, Fesofi 3198).
Cualquier emparejamiento va **sello a sello**, nunca `min → min` de la serie.

## Lo que hay que decidir antes de A1

1. **Clave de Colnect**: pedirla (gratuita, por solicitud) o descartar también
   Colnect. Sin clave, A3 no se puede ni probar: la CAPI responde 401.
2. **Delcampe**: descartar (recomendado, `robots.txt` prohíbe la búsqueda),
   agregador de pago, o dejarlo para más adelante. A4 queda condicionado.
3. **Fesofi como fuente de identidad en A6**: sí/no. No cuesta nada y no necesita
   clave; cambia el alcance de A6 y de A9.
4. **Iberphil**: fuera de la primera versión (recomendado) o dentro sólo para
   clásicos y series completas.
5. **Dónde se lanza la investigación** (sigue abierta desde el plan): DataDesk,
   la app Flet, o un comando `manage.py`.

## Efecto sobre el plan

- A2: la dependencia es `httpx[http2]` (el contenedor no trae `h2`).
- A3: sin cambios, pero bloqueado por la clave.
- A4: se reduce a «agregador de pago o nada»; el scraping queda descartado.
- A6: gana Fesofi (`?sku=`), que resuelve Edifil, título, facial y tirada.
- A7: la valoración empieza con Colnect (`/market_prices`, `/item_sales`);
  Iberphil entra después, si entra, a nivel de lote.
- A9: el LLM pierde también el papel de «catálogo» cuando Fesofi responde.
