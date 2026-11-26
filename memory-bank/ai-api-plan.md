# AI API — plan de mejora con fuentes reales

**Estado: en marcha (2026-11-25). A0 hecho; A1–A10 sin empezar.** Este documento
existe para no volver a investigar las fuentes ni a redescubrir los defectos del
módulo cuando se retome, y §7 guarda lo que ya se ha hecho y decidido.

Se dispara porque, usándolo, el conocimiento de filatelia española de los LLM es
bastante limitado: los códigos y las descripciones salen, pero los precios de
mercado y muchos datos técnicos son invención del modelo. El objetivo es que el
endpoint obtenga los datos de fuentes reales —Fesofi para identidad y hechos de
catálogo, Colnect para el mercado, y una búsqueda en sitios permitidos para el
precio orientativo— y que el modelo sólo redacte lo que las fuentes sostienen.

---

## 1. Estado actual del módulo (analizado 2026-11-24)

`backend/ai_api/` (~1.500 líneas + ~1.700 de tests, 99 tests verdes):

Pipeline de `POST /api/v1/issues/extraction/`:

```
SearchService (Serper, site:catalogodesellos.fesofi.es)
  → ScrapingService (links "resto valores serie", tablas de la ficha)
  → clean_scraped_data (serie_info común + stamps únicos, desc 180 chars)
  → LLMService → ProviderFactory → GeminiProvider | GroqProvider
      (si sellos > LLM_BATCH_SIZE=5: cabecera + N lotes)
  → SeriesExtractionResponseSerializer → envoltura estándar del renderer
```

Defectos encontrados, que A2/A9 corrigen de paso:

| # | Defecto | Efecto |
|---|---|---|
| 1 | El prompt manda "busca en Colnect, Delcampe e Iberphil" y "verifica precios realizados" sin herramienta de búsqueda, y a la vez "never use internal knowledge" + "EXPANSION: use your internal knowledge" | Los `market_value_*` son inventados; el prompt se contradice |
| 2 | Se aplica un factor de corrección −25% y una regla "la serie no puede valer más que la suma de sus sellos" | Cifras inventadas sobre datos inventados |
| 3 | SSRF: con `name` = URL y `date` = "0" se descarga cualquier host (`_is_valid_url` además tiene un bug: `([www]\.)?` es una clase de caracteres) | El endpoint es un proxy HTTP autenticado |
| 4 | `requests.post(SERPER_URL)` sin timeout | Un Serper lento bloquea un worker de gunicorn |
| 5 | `LLMService` y ambos providers hacen `except Exception: raise Exception(...)` | El 422 de la vista nunca se dispara en producción; todo es 500 |
| 6 | Scraping vacío → `clean_scraped_data` = `{}` → `clean_data.get("serie_info").get(...)` = `AttributeError` | "No encontrado" se responde como 500 |
| 7 | `stamps` es `ListField(DictField)`; `StampDetailSerializer` no se usa | Un `amount_printed` string o un `color` ausente llegan al cliente |
| 8 | Gemini lee de `settings`, Groq de `os.getenv`; el factory también de `os.getenv` | Dos fuentes de verdad para lo mismo |
| 9 | `SeriesExtractionView` no está en `USER_VIEWS` | Solo pasa la master API key; un JWT recibe 403 |
| 10 | `frontend/core/urls.py:47` define `issues_extraction` sin consumidor | Código muerto (la página de IA desapareció) |

Cosas que ya están bien y no se tocan: separación provider/factory, `BaseLLMProvider`
con prompt + limpieza de JSON + orquestación de lotes, y los tests con servicios
mockeados (sin red).

---

## 2. Reconocimiento de las tres fuentes (2026-11-24)

| Fuente | Qué ofrece | Acceso | Límites | Qué aporta aquí |
|---|---|---|---|---|
| **Colnect** | Catálogo de sellos y **precios de mercado**: `/item` (1–50 ids), `/list`, `/list_id`, `/search`, `/market_prices`, `/item_sales`, `/request_count` | API oficial CAPI: `appId` + `appSecret`, firma **HMAC-SHA256** sobre `path>|<timestamp>`, cabeceras `Capi-Timestamp` / `Capi-Hash`, **HTTP/2 obligatorio** (HTTP/1.x → 426), User-Agent identificable de 16+ caracteres | Clave por formulario, gratis para servicios gratuitos; cuotas **diarias, semanales y mensuales** (los clientes existentes manejan "Limits exceeded daily/weekly/monthly") | La fuente principal: datos de catálogo y precios reales, y el código Edifil como clave de emparejamiento |
| **Delcampe** | Anuncios y ventas de sellos | API oficial **solo de vendedor** (`/seller`, `/item`, `/item/opened`, `/item/closed`, `/item/sold`…): gestiona *tus* artículos, **no busca el mercado** | 180 req/min, 10.000 altas/día | Solo sirve vía scraping de la web o agregador de pago (ReefAPI y similares ofrecen `search` con `status: sold`, 3 créditos por llamada) |
| **Iberphil** | Resultados de subasta con **adjudicación por lote** y listas de "lotes vendidos después de la subasta" con precio de salida | HTML público (subasta → `informacion-de-subasta` / `auction-sold-lots`) | Sin API; son **lotes**, no sellos sueltos | Datos reales de remate para clásicos y series completas. Ejemplo #131: 1.781 ofrecidos, 888 vendidos, 132.784 € |

Aviso práctico: desde el devcontainer, Colnect e Iberphil dieron **timeout** en
`webfetch` directo. La prueba A0 debe hacerse contra la API (o desde otro host),
no con un fetch simple; eso no dice nada sobre su disponibilidad real.

> **Lo que A0 midió de verdad (2026-11-25)** está en `ai-sources-spike.md` y
> resumido en §7. De esta tabla, dos cosas cambian: Delcampe queda **fuera del
> plan** (`robots.txt` prohíbe su búsqueda) e Iberphil **fuera de la primera
> versión** (martillo sólo en algunas subastas y sin código de catálogo). Y entra
> una cuarta fuente que no estaba: **Fesofi**, con Store API pública y exacta por
> `sku`. La tabla se deja como se escribió, como registro de la investigación
> previa.

---

## 3. Decisiones abiertas (bloquean pasos)

1. **Clave CAPI de Colnect**: el procedimiento está en A3
   (`colnect.com/en/capi/use_request`). El usuario aún no la ha pedido. Bloquea A3,
   no A1, A2 ni A6.
2. **Dónde se dispara la investigación**: DataDesk, app Flet, o solo un comando.
   Condiciona A8 (y si hace falta cola).
3. **Qué motor usa opencode**: el **proveedor** está decidido y hecho —opencode,
   con Gemini y Groq ya fuera del código—, y el **modelo** se elige en
   `OPENCODE_MODEL`, sin tocar código. No bloquea ningún paso; el valor se decide
   cuando haya una tubería que ejecutar.

Cerradas en A0 (2026-11-25): Delcampe, Iberphil, Fesofi sí, media recortada y
lista de sitios permitidos. Detalle en §7. **Serper se queda de momento**, y se
quitará si la búsqueda de precios no lo necesita.

---

## 4. Pasos

Dependencias: A0 → A1 → A2 → A6 → A7 → A8 → A9 → A10. A1b (proveedor opencode)
ya está hecho. A3 (Colnect) entra en cuanto exista la clave CAPI, en paralelo a A6.
A4 y A5 están fuera del plan (decidido 2026-11-25: Delcampe por `robots.txt`,
Iberphil por fuente débil).

| Paso | Qué | Tamaño | Depende de | Estado |
|---|---|---|---|---|
| A0 | Prueba de fuentes | S | — | **hecho 2026-11-25** |
| A1 | Contrato y modelo de observaciones | M | A0 | **hecho 2026-11-25** |
| A1b | Proveedor opencode (fuera Gemini y Groq) | S | — | **hecho 2026-11-25** |
| A2 | Capa de fuentes + arreglos de seguridad | M | A1 | **hecho 2026-11-26** |
| A3 | Adaptador Colnect | L | A2, clave CAPI | pendiente, bloqueado por la clave |
| A4 | Adaptador Delcampe | M | — | **fuera del plan** |
| A5 | Adaptador Iberphil | M | — | **fuera de la 1.ª versión** |
| A6 | Identidad y emparejamiento (Fesofi primero) | L | A2 | **en curso**: nombre parcial hecho 2026-11-26 |
| A7 | Valuación (media recortada) | S | A6 | pendiente |
| A8 | Ejecución (síncrona con presupuesto + backfill) | M | A7 | pendiente |
| A9 | LLM reducido y validador de fuentes | S | A7 | pendiente |
| A10 | Cierre: docs, esquema, tests, memory-bank | S | todo | pendiente |

### A0 — Prueba de fuentes (S) — **HECHO 2026-11-25**

`manage.py ai_sources_probe` que, para cinco series conocidas, intenta: Colnect
`/item` por código Edifil, búsqueda en Delcampe y una subasta de Iberphil. Guarda
código HTTP, forma de la respuesta, `robots.txt` y notas de ToS de cada dominio.

Salida: `memory-bank/ai-sources-spike.md` con la decisión sobre Delcampe. Decidió
el alcance de A4 — y lo decidió en contra: ver más abajo.

Aceptación: el documento existe con las cinco series, los códigos HTTP reales y la
decisión escrita sobre cada fuente. **Cumplida.**

**Hecho el 2026-11-25.** Resultados en `memory-bank/ai-sources-spike.md`, evidencia
cruda en `ai-sources-spike.json`, comando `manage.py ai_sources_probe`
(`ai_api/probe.py` + `ai_api/management/commands/ai_sources_probe.py`, 27 tests sin
red en `ai_api/test/test_probe.py`). Resumen: Colnect responde 426 en HTTP/1.1 y
401 en HTTP/2 (la red llega, falta la clave) y su sitio público está tras Anubis;
Delcampe prohíbe en `robots.txt` la ruta de búsqueda, así que **el scraping queda
descartado**; Iberphil sólo publica el martillo en algunas fichas y sin códigos;
y **Fesofi, que no estaba en el plan, expone una Store API pública y exacta
(`?sku=`) con `Número EDIFIL`, título de serie, facial, tirada, color y dentado**.

### A1 — Contrato y modelo de datos (M) — **HECHO 2026-11-25**

El cambio de fondo: el endpoint deja de devolver cifras que nadie puede auditar y
devuelve **observaciones con fuente**.

- Modelo `SourceObservation`: `source` · `external_id` · `url` · `subject`
  (FK a `Stamp` o `Issue`) · `kind` (`sold` / `ask` / `auction_hammer`) · `price` ·
  `currency` · `condition` · `observed_at` · `raw` (JSON) · `raw_hash` (dedupe).
- Respuesta: `sources`, `observations` y
  `valuation: {estimate, currency, sample_size, method, as_of}`, más `gaps` (qué no
  se encontró y por qué).
- Prompts: fuera la sección de valuación entera y fuera el "EXPANSION con
  conocimiento interno". La descripción del LLM se marca
  `description_source: "llm"` para que no se confunda con un dato de catálogo.

Aceptación: migración aplicable y reversible; serializers de la respuesta con los
campos nuevos; tests de contrato con datos fijos.

**Hecho el 2026-11-25.** Lo que hay, con las decisiones que se tomaron al
implementarlo:

- `backend/ai_api/models.py` con `SourceObservation`. La migración se genera y se
  aplica en local, pero **`migrations/` está gitignoreado** (`.gitignore:70`): CI
  construye el esquema desde los modelos. Comprobado que aplica y revierte
  (`migrate ai_api zero` y vuelta).
- `subject` son **dos FK anulables** (`issue`, `stamp`) más un `CheckConstraint`
  que exige exactamente una, en vez de un `GenericForeignKey`: se consulta sin
  `contenttypes` y el error salta en la base, no en Python.
- `kind` tiene **cuatro** valores, no tres: `catalog`, `ask`, `sold` y
  `auction_hammer`. El de catálogo entró con la decisión del 2026-11-25 (un precio
  de Edifil no es ni una oferta ni una venta y hay que poder distinguirlo).
- `raw_hash` es la identidad de la observación: fuente, id externo, sujeto, tipo,
  condición, precio y divisa; **la fecha no entra**, para que ver el mismo precio
  dos veces no duplique la fila y un precio distinto sí quede como histórico.
  `unique=True` y se calcula en `save()`.
- Respuesta (`api/serializers/observation_serializer.py`): `Observation`,
  `SourceReport`, `Gap` y `Valuation` (`estimate`, `min`, `max`, `currency`,
  `sample_size`, `method`, `sources`, `as_of`). En `sources` el campo se llama
  `source` y no `name` a propósito: con dos campos distintos para el mismo
  `choices`, drf-spectacular avisaba de un enum duplicado.
- `description_source` por defecto `llm`, y `to_representation` se lo pone también
  a cada sello. Los prompts ya no piden cifras; el texto se escribe sólo con lo que
  trae la entrada y `notes` queda vacío si la fuente no dice nada.
- `market_value_mnh` / `market_value_used` siguen en la forma por compatibilidad,
  pero son `required=False` y **el endpoint los pone a `null`** aunque el proveedor
  escriba algo (serie y sellos): hasta que A7 los calcule desde observaciones, un
  número ahí no se puede auditar. A9 añade el validador que lo hace cumplir para
  todos los campos factuales.
- 22 tests nuevos: 15 del modelo (`test_observations.py`: identidad, duplicados,
  precio distinto, sujeto, defaults) y 7 de contrato (`test_contract.py`: ida y
  vuelta completa, payload antiguo con defaults, etiqueta de procedencia, fuente
  desconocida rechazada, valuación sin estimación, y el endpoint devolviendo nulos
  aunque el mock escriba precios). **1.655 tests verdes**; esquema OpenAPI sin
  avisos.


### A1b — Proveedor opencode (S) — **HECHO 2026-11-25**

La API deja de hablar con Gemini y Groq y pasa a hablar con **opencode**, que es el
único proveedor. El **motor** (el modelo concreto) se decide más adelante y no vive
en el código: va en el cuerpo de la petición, no como constante.

**Cómo se llama (comprobado 2026-11-25)**: por la **API de inferencia** del Console
de opencode, `https://opencode.ai/inference/...`, con
`Authorization: Bearer oc_sk_…`. Es compatible con OpenAI, Anthropic y Gemini, así
que el backend hace HTTP normal y **no necesita instalar opencode ni levantar
`opencode serve`**: la clave que se crea en el Console es para inferencia, no para
autenticar clientes de `serve` (eso es `OPENCODE_PASSWORD` o emparejamiento).

- `ai_api/services/opencode_provider.py` con `OpenCodeProvider(BaseLLMProvider)`,
  misma firma `series_extract(name, date, clean_data)`; el troceado, el parseo del
  JSON y los reintentos siguen en `BaseLLMProvider`.
- Se usa **una sola familia de API** para no tener tres caminos: la de *OpenAI chat
  completions* (`/inference/openai/v1/chat/completions`). La tabla del Console
  lista el endpoint **nativo** de cada modelo —GPT por *Responses*, Claude/Qwen por
  *Messages*, Gemini por *generateContent*— pero la documentación dice que
  **Console traduce todo modelo de texto a las demás APIs**, así que también se
  puede elegir uno de esos desde el mismo adaptador. (Corregido el 2026-11-25: la
  primera lectura decía que hacía falta una rama por familia.)
- Configuración nueva: `OPENCODE_API_KEY` (mejor una clave de **service account**
  que una personal: no depende de una persona y tiene su propio presupuesto),
  `OPENCODE_MODEL` y, opcional, `OPENCODE_BASE_URL`.
- `provider_factory.py`: el registro pasa a `{"opencode": OpenCodeProvider}` y
  `LLM_PROVIDER` por defecto `opencode`.
- **Se borran** `gemini_provider.py`, `groq_provider.py` y sus tests, las claves
  `GEMINI_*` / `GROQ_*` de `settings.py` y de `.env.example`, y las dependencias
  `google-genai` y `groq`. Ninguna de las dos debe quedar en `requirements`.
- `LLM_BATCH_SIZE` se queda: el troceado es cosa del proveedor base, no del motor.
- **Serper se queda de momento.** `SERPER_*` y `SearchService` no se tocan aquí; A2
  sigue arreglándole el timeout que hoy no tiene. Si la búsqueda de precios acaba
  resolviéndose sin él, se quita en un paso aparte.

**Aviso de facturación, leído en la documentación del Console**: los modelos de la
capa gratuita **sólo funcionan desde dentro de opencode**; cualquier otro cliente
recibe `403` aunque tenga clave. Para que el backend llame, hay que usar modelos de
pago o una suscripción Go. Eso invalida la idea de «modelo gratis para el volumen»:
el reparto bueno/barato se hará entre modelos de pago.

**Aviso que conviene no perder**: cambiar de proveedor no cambia la epistemología.
El modelo, por esta vía, es una completación sin herramientas: puede inventar igual
que Gemini. La diferencia llega cuando el que investiga es un agente con acceso a
Fesofi, Colnect y la búsqueda — eso es A2/A3/A6, no A1b.

Aceptación: `ProviderFactory.create_provider()` devuelve el proveedor de opencode;
no queda ninguna referencia a Gemini ni Groq en código, settings, `.env.example` ni
tests; la suite sigue verde con un transporte falso (sin red); y una llamada real
documentada contra `/inference/openai/v1/chat/completions` con el modelo elegido por
configuración.

**Hecho el 2026-11-25.** Lo que hay, y las decisiones que se tomaron al
implementarlo:

- `ai_api/services/opencode_provider.py`: lee `settings` (no `os.getenv`, que era el
  defecto 9 de §1), hace `POST` a `{OPENCODE_BASE_URL}/chat/completions` con
  `Authorization: Bearer`, el modelo en el cuerpo, `temperature: 0`,
  `response_format: {"type": "json_object"}` y `max_tokens` de
  `OPENCODE_MAX_TOKENS`. En un error registra **el código y el principio del
  cuerpo**, que es lo que distingue una clave mala (401) de un modelo no disponible
  para esa cuenta (403) de un límite (429); en cada llamada registra el `usage`, que
  en el Console trae el coste.
- **`series_extract` se movió a `BaseLLMProvider`.** Estaba duplicado palabra por
  palabra en los dos proveedores y habría sido la tercera copia: ahora el flujo
  (una llamada para series pequeñas, cabecera + lotes para grandes, fusión) vive una
  vez y el proveedor implementa sólo los tres ganchos. `Messages` se importa allí.
- `provider_factory.py`: una sola entrada y **sin `LLM_PROVIDER`**. Con un único
  proveedor, una variable de entorno que sólo admite un valor válido es una forma
  de romper un despliegue con un valor viejo; ahora un `LLM_PROVIDER=gemini`
  olvidado en un `.env` no hace nada (hay dos tests que lo fijan a propósito).
- `settings.py`: entran `OPENCODE_API_KEY`, `OPENCODE_MODEL`, `OPENCODE_BASE_URL`,
  `OPENCODE_TIMEOUT` (120 s) y `OPENCODE_MAX_TOKENS` (8192); salen `GEMINI_*`,
  `GROQ_*` y `LLM_PROVIDER`. `LLM_BATCH_SIZE` se queda.
- **Borrados**: `gemini_provider.py`, `groq_provider.py`, `test_gemini_provider.py`,
  `test_groq_provider.py`, `test_batch_processing.py` (sus cinco tests del troceado
  ya estaban en `test_base_llm_provider.py`) y
  `validate_multi_provider_implementation.py`; y las dependencias `google-genai` y
  `groq` de `requirements.base.txt`.
- `messages.py`: `missing_api_key()` / `missing_model_name()` ya no dicen
  `GEMINI_*`; hablan de `OPENCODE_API_KEY` / `OPENCODE_MODEL`. README y docstrings
  del módulo, de la vista y de `LLMService` actualizados.
- Tests: 33 en los tres archivos (16 del proveedor —configuración, petición,
  respuesta, fallos y flujo con lotes—, 8 de la factoría y 9 de la fachada). La
  suite completa queda en **1.628** (antes 1.655: se borraron 60 tests de los cinco
  archivos viejos y se añadieron 33).

**Verificado en real el 2026-11-25**: con `OPENCODE_API_KEY` y
`OPENCODE_MODEL=glm-5.3-flash` en el `.env`, una extracción desde Swagger pasó la
tubería entera y devolvió la forma de A1 —`description_source: "llm"`, `sources` y
`observations` vacíos, `valuation: null`, los `market_value_*` a `null` y una
descripción sin precios—. La aceptación del paso queda cumplida. El `.env` de cada
entorno necesita el cambio: fuera `GEMINI_*` / `GROQ_*` / `LLM_PROVIDER`, dentro
`OPENCODE_API_KEY` y `OPENCODE_MODEL`.

**Lo que se vio al usarlo (para A2)**: tarda. Medido con el código del repo, el
scraping no es el culpable —6 sellos son 1,7 s (0,3 de índice + 1,4 de las seis
fichas); 29 sellos, 7,0 s—, sino las **llamadas al modelo**, que son
`1 + ceil(n / LLM_BATCH_SIZE)` y todas en serie: con el lote en 5, una serie de 6
sella hace 3 llamadas y la de 57 haría 13. Palanca inmediata: `LLM_BATCH_SIZE=15`
(6 sellos → 1 llamada, 57 → 5), que es sólo configuración y sale más barato porque
el contexto de la serie se repite menos. Lo demás es de A2: paralelizar el scraping
con límite por dominio, cachear, y registrar `elapsed_ms` por llamada para dejar de
adivinar. Dos hallazgos más del uso: `SearchService` se traga el fallo cuando
`SERPER_*` está vacío y la vista lo cuenta como «no se encontró nada» (404), y la
vista lee `título serie` / `fecha de emisión` de `serie_info` cuando el limpiador
devuelve `issue_name` / `issue_date`, así que el nombre llega al log como `None`.

### A2 — Capa de fuentes (M) — **HECHO 2026-11-26**

`ai_api/sources/base.py` con `SourceAdapter` (`name`, `supports(subject)`,
`fetch(subject) -> list[Observation]`), `http.py` con allowlist de dominios,
timeouts, reintentos con jitter, límite por dominio, caché y User-Agent
identificable, y `registry.py`.

Aquí se cierran además los defectos 3, 4, 5, 6, 8 y 9 de §1: allowlist
(`catalogodesellos.fesofi.es`, `api.colnect.net`, y los sitios de precio permitidos:
`todocoleccion.net`, `ebay.es` / `ebay.com`), timeouts en Serper —que sigue vivo
hasta que se decida—, 404/422/500 con significados distintos, y una sola fuente de
configuración.

Dependencia nueva: `httpx` (HTTP/2; `requests` no lo hace y CAPI lo exige).

Aceptación: tests de `http.py` con un servidor falso (allowlist, timeout, reintento,
límite); ningún test toca la red.

**Lo que dejó el primer uso real (2026-11-25), para este paso:**

- **El scraping es secuencial**: una petición por sello, una detrás de otra. Medido:
  6 sellos 1,4 s, 29 sellos 6,8 s (~0,23 s por ficha). `http.py` debería traer un
  pool pequeño con **límite por dominio** y caché, no sólo timeouts.
- **`SearchService` se traga el fallo**: con `SERPER_*` vacío pide `None`, registra
  «Invalid URL 'None'» y devuelve `None`; la vista lo cuenta como
  «no se encontró nada» (404). Un error de configuración no puede parecer un dato
  que no existe: es el defecto 3 de §1 y aquí tiene su caso concreto.
- **Lectura muerta en la vista**: saca `name` / `date` de `serie_info` con las claves
  `título serie` / `fecha de emisión`, pero `clean_scraped_data` devuelve
  `issue_name` / `issue_date`. Hoy sólo ensucia el log (`series: None`).
- **Falta saber cuánto tarda cada llamada al modelo**: añadir `elapsed_ms` al log del
  proveedor es una línea y convierte «tarda bastante» en un número.
- **El lote del modelo** es `1 + ceil(n / LLM_BATCH_SIZE)` llamadas en serie. Subirlo
  a 15 es configuración, no código, y es la palanca más barata mientras A2 llega.

**Hecho el 2026-11-26.** Qué hay, y lo que se decidió al implementarlo:

- `backend/ai_api/sources/` con cuatro piezas: `http.py` (el `HttpClient`: allowlist
  por host, timeouts de conexión y lectura, reintentos con jitter sólo para 5xx/429,
  límite por host con semáforo, caché TTL de los 200, User-Agent propio y un
  singleton de proceso para que la caché y los límites sirvan de algo), `errors.py`
  (`SourceError` y sus cuatro hijos, uno por significado), `base.py`
  (`SourceAdapter` con `supports`/`fetch`, devolviendo observaciones sin guardar) y
  `registry.py` (nombre → adaptador; hoy vacío, A3 y A6 registran).
- `SearchService`: pasa por el cliente. **Sin `SERPER_URL`/`SERPER_API_KEY` lanza
  `SourceConfigurationError`**; si el backend contesta 401/403, igual; si contesta
  4xx/5xx, `SourceUnavailable`; `None` queda para «funcionó y no hay página».
- `ScrapingService`: pasa por el cliente y **descarga en paralelo** con un pool
  acotado por el límite por host; el parseo se queda fuera del hilo. Medido con la
  serie de 29 sellos: **7,0 s → 0,9 s** (y 0,31 s la segunda vez, con caché); la de
  6 sellos, 1,7 s → 1,2 s.
- El proveedor registra **`elapsed_ms`** junto al `usage`, así que «tarda» ya es un
  número. `BaseLLMProvider` y `LLMService` dejan de envolver `ValueError`, y el 422
  de la vista vuelve a existir: un JSON que no parsea o una respuesta vacía ya no
  acaban en 500.
- La vista: **el atajo de la URL exige allowlist** (antes cualquier host, SSRF) y un
  host no permitido da 400; `serie_info` se lee con `issue_name`/`issue_date`; un
  scrape vacío es 422 con motivo, no un 500 escondido; y los errores se separan —
  400 host no permitido, 404 «no hay nada», 422 contrato, 500 configuración, 502
  fuente caída.
- **Defecto 9 (§1) cerrado por decisión**: `SeriesExtractionView` **no entra en
  `USER_VIEWS`**. Sigue siendo master-key only: el pipeline no está paginado por
  usuario y dejar que cualquier JWT lo dispare es dejar que gaste dinero. Los dos
  tests de 403 que ya existían lo fijan.
- Dependencia: `httpx[http2]==0.28.1` (el extra lo necesita A3; A2 no usa HTTP/2).
  Los loggers de `httpx`/`httpcore` bajados a WARNING en `log_setup`, porque a DEBUG
  escriben una línea por cada byte del protocolo.
- Tests: 35 nuevos (`test_source_http.py` 22, `test_source_registry.py` 7,
  `test_scraping_service.py` 6) más los de la vista (400 host no permitido, 502
  fuente caída, 500 configuración, 422 scrape vacío). **1.664 verdes**, ningún test
  toca la red (todo va por `httpx.MockTransport`).
- **Lo que NO trae**: los adaptadores de verdad (A3 y A6), la valoración (A7) y
  sustituir Serper. Sigue vivo, con timeout y errores que significan algo.

### A3 — Colnect (L)

Adaptador con firma HMAC, `/item` por código Edifil (hasta 50 ids por llamada),
`/market_prices` y `/item_sales`; lectura de `/request_count` antes de gastar
cuota; caché de 7 días.

Aviso de cobertura: **Edifil falta en 2.761 de 9.557 sellos y en 696 series**
(dato de S36). Esos sellos necesitan el fallback de A6 — y el fallback es Fesofi,
que devuelve el `Número EDIFIL` en 2.733 de esos 2.761.

Aceptación: tests con JSON grabado; una llamada real documentada en el spike.

> **Cómo se pide la clave (comprobado 2026-11-25).** El sitio vivo es
> **`https://colnect.com/en/capi/use_request`**, con la sesión de Colnect abierta.
> El formulario antiguo de LimeSurvey (`survey.colnect.info/…sid=167713`) sigue
> respondiendo 200 pero encabeza con «UPDATE: do not fill this survey but rather
> apply directly on Colnect here»: hay que usar el de la web.
>
> Pide: nombre completo, **usuario de Colnect**, organización, correo, Facebook,
> método de contacto preferido, teléfono y dirección postal; qué vas a construir
> (explicación detallada) y con qué tecnología; si has hecho algo parecido antes;
> si estás afiliado a algún servicio para coleccionistas; **peticiones concurrentes
> y totales por día**; y **desde qué servidor saldrán** (IP o dominio). Se firma
> aceptando los ToS, que es donde está la sección de CAPI.
>
> **La puerta que hay que leer dos veces:** la propia página dice «CAPI is meant
> for providing collectors worldwide with innovative solutions. **It is not meant
> for one person's collection**». La app es un gestor de colecciones con usuarios,
> colecciones y API, así que se puede presentar como lo que es —una herramienta
> para coleccionistas— pero no como «mi base de datos». Si el proyecto se plantea
> como algo privado, la respuesta será no.
>
> Datos técnicos que ya conocemos y que conviene poner en la solicitud:
> **sólo HTTP/2**, firma **HMAC-SHA256** en `Capi-Timestamp` + `Capi-Hash` sobre
> `ruta + ">|<" + timestamp`, User-Agent que identifique la app (16+ caracteres) y
> `GET /request_count` para vigilar la cuota. Los `robots.txt` de Colnect dicen
> literalmente que usar sus datos por medios automáticos está prohibido sin
> consentimiento escrito: la CAPI es la única puerta, también para el precio.

### A4 — Delcampe (M) — **eliminado del plan (2026-11-25)**

Mismo interfaz que A3, con dos implementaciones posibles: adapter de scraping
(búsqueda por código Edifil + año; solo se aceptan anuncios cuyo título contenga
código y año; caché 7 días) o adapter sobre agregador de pago con `status: sold`.
Si A0 dice que bloquea o que su ToS no lo permite, **se descarta** y el plan sigue
sin él: mejor perder una fuente que un scraper que nos bloqueen.

> **A0 (2026-11-25): descartado el scraping.** `robots.txt` prohíbe
> `/en_GB/collectables/search` (y las rutas equivalentes en los otros idiomas), que
> es justo la que necesita un buscador por código. La búsqueda existe y devuelve lo
> que buscamos con `term=<código> <año>` (ver el spike), pero usarla va contra
> `robots.txt`.
>
> **Decisión del usuario (2026-11-25): Delcampe sale del plan**, tampoco por
> agregador de pago. Si algún día hace falta, es un adaptador nuevo, no este paso.

Aceptación: tests con HTML/JSON grabado; el filtro de título rechaza anuncios que
solo comparten el año.

### A5 — Iberphil (M) — **fuera de la primera versión**

Parseo de las tablas de resultados por subasta (lote, clasificación, precio de
salida, adjudicación). El emparejamiento es contra **la serie**, no contra el
sello: año, nombre y rango de códigos mencionados en la descripción del lote, con
umbral conservador. Sin match claro no hay observación.

> **Decisión del usuario (2026-11-25): Iberphil queda fuera de la primera
> versión.** Motivo de A0: la tabla de vendidos sólo trae la puja inicial, el
> martillo aparece en algunas fichas y en otras no, y ninguna descripción lleva
> código de catálogo. El código del adaptador se escribirá si más adelante hace
> falta para clásicos; no se borra del plan.

Aceptación: tests con una subasta grabada; una serie sin lote comparable produce
`gaps`, no una observación falsa.

### A6 — Identidad y emparejamiento (L) — **en curso (primera rebanada hecha)**

Orden: código Edifil normalizado → año + facial + color + nombre de serie
(solapamiento de tokens) → nada. Cada candidato se guarda con `score` y URL; por
debajo del umbral no se usa para valorar, solo se lista en `gaps` para revisión
humana en DataDesk.

> **A0 (2026-11-25): nuevo primer escalón.** El código **Fesofi** resuelve contra
> la Store API pública de `catalogodesellos.fesofi.es` (`?sku=<código>`, JSON sin
> clave) y devuelve el `Número EDIFIL`, el `Título Serie`, el facial, la tirada, el
> color y el dentado. Con eso la identidad deja de depender del LLM en la mayoría
> de los casos. Dos avisos del spike: `min(edifil)` y `min(fesofi)` de una serie no
> son el mismo sello (emparejar **sello a sello**), y 1 de las 5 series probadas no
> está indexada por `sku`.
>
> **Decisión del usuario (2026-11-25): Fesofi es la primera fuente de identidad.**
> Además del título y los códigos, trae `Motivo Sello`, `Facial`, `Color`,
> `Dentado`, `Impresión`, `Imprenta`, `Tirada`, `Tipo De Correo` y `Valores De La
> Serie`, que son hechos de catálogo para rellenar la ficha sin inventar. **No trae
> precios** (todos los `price` son 0): no sirve para valorar.

Aceptación: juego de pares conocidos (aciertos y errores deliberados); ningún falso
positivo por debajo del umbral llega a la valuación.

**Primera rebanada hecha el 2026-11-26: encontrar la serie por nombre parcial.**

El problema que la disparó: la búsqueda de Serper pedía `site:… "navidad" "1986"`,
dos frases literales, y con eso «no encontraba nada» aunque Google devuelva el
enlace en el primer resultado. Lo que se quería —y ahora se hace— es que la serie
salga cuando su nombre **contiene** las palabras, no cuando coincide exacto.

- `ai_api/sources/fesofi.py` (`FesofiCatalogue`) pregunta a la Store API por
  **atributos**: `Título Serie` (`pa_titulo-serie`, id 5) **y `Motivo Sello`**
  (`pa_motivo-sello`, id 6), más `Año de Emisión` (`pa_ano-de-emision`, id 22) como
  filtro. El buscador de términos es **parcial** y no distingue mayúsculas, que es
  justo lo que hacía falta. El motivo entra porque `name` puede ser el de un sello
  suelto: «la sagrada familia» es el motivo del sello de 1986, cuya serie se llama
  «Navidad 1986».
- El nombre se parte en palabras (sin acentos, sin mayúsculas, sin stopwords como
  «de»), los años de cuatro cifras se separan como año y no cuentan como palabra, y
  se piden los términos de cada palabra. Los candidatos se ordenan por **cuántas
  palabras cubren** y luego por nombre más corto; se prueban **todos**, no sólo el
  mejor, porque el primer candidato puede no tener productos en ese año.
- Comprobado contra el catálogo real: `navidad 1986` → 2884 y 2883 (Edifil 2867 y
  2868); `la sagrada familia 1986` → 2883 por el **motivo** («La Sagrada Familia.
  Valladolid»), y el scrape da la serie entera («Navidad 1986», 2867 y 2868);
  `castillos de españa 2007` → 4605 (la serie de 2007 está bajo el término
  «Castillos», no «Castillos de España»); `expo 92` → 2960; `isabel ii 1850` →
  0005-2… (5 páginas); `quijote 1998` → 3601.
- `SearchService.find_series_url` pasa a ser un **localizador**: primero el
  catálogo, y si no hay nada, Serper. Un fallo del catálogo se registra y se cae al
  fallback en vez de tumbar la búsqueda.
- **Bug encontrado al probarlo**: la caché de `HttpClient` indexaba por URL sin la
  query, así que `/products?term=1` y `/products?term=2` compartían entrada y
  «castillos» devolvía los sellos de Navidad. La query entra ahora en la clave, con
  su test.
- El candidato guarda **de qué atributo** salió, y la consulta de productos filtra
  por ese atributo: un motivo se busca como motivo, no como título de serie. Se
  prueban como mucho 10 candidatos (cada uno es una petición) y el orden es
  cobertura, serie antes que motivo, nombre más corto y `id`.
- Lo que **falta de A6**: leer los hechos del producto desde la Store API en vez de
  scrapear el HTML, el matcher con `score` y los `gaps`, y decidir cuándo el
  catálogo gana a la heurística. `quijote 1998` ya devuelve algo (3601, por motivo);
  falta comprobar que sea el sello y no la hoja del primer día.


### A7 — Valuación (S)

`valuation.py`: filtra por condición, convierte divisa con tasa y fecha guardadas,
calcula **mediana e IQR** y exige `n ≥ 3` por condición; si no llega, `null` y un
gap. Sin factor −25%. La regla "la serie no puede valer más que la suma" queda, si
se conserva, como aviso, nunca como modificador.

Aceptación: tests de mediana con muestras pequeñas, divisas mezcladas y `n < 3`.

### A8 — Ejecución (M)

Una request no hace 3 scrapes + LLM. Primero **síncrono con presupuesto**: 5–8 s
por fuente, 25 s total, `partial: true` con las fuentes pendientes, y caché para que
la segunda llamada termine lo que falta. El backfill de 9.558 sellos va por comando
por lotes (`--limit`, `--source`, `--dry-run`), nunca por el endpoint. Si el uso
crece, entonces cola y contenedor de worker (hoy no hay Celery ni Redis, y no se
meten para esto todavía).

Aceptación: una fuente caída no tumba la respuesta; el presupuesto se respeta; el
comando de backfill no repite observaciones (`raw_hash`).

### A9 — LLM reducido (S)

Normalizar texto y desambiguar candidatos, nada más. Un validador rechaza cualquier
campo factual de la respuesta cuyo valor no venga de una observación con fuente.

Con A1b, «el LLM» es siempre opencode; el motor que use por dentro es indiferente
aquí, porque lo que se mide es que la respuesta sólo traiga lo que las fuentes
sostienen.

Aceptación: un test alimenta un resultado del LLM con un `market_value` sin
observación y el validador lo anula.

### A10 — Cierre (S)

README reescrito (fuentes, cuotas, ToS, códigos de error, qué no se puede obtener),
esquema actualizado en drf-spectacular, tests de contrato por fuente con respuestas
grabadas, y `activeContext.md` / `progress.md` al día.

---

## 5. Lo que el plan no promete

- Que Colnect tenga el sello buscado: su catálogo español está bien, pero no es
  Edifil completo.
- Que Delcampe se deje leer.
- Que Iberphil tenga un lote comparable para cada serie moderna.

El plan está construido para que esas ausencias salgan como `gaps` explícitos y no
como números inventados.

---

## 6. Cifras de partida (de S36, 2026-11-22)

- 2.541 series y 9.558 sellos.
- Edifil ausente en **2.761 sellos** y **696 series**; Fesofi ausente en **61** y **6**.
- Serie más larga: 57 sellos.

---

## 7. Registro de implementación

### 2026-11-25 — A0 hecho (prueba de fuentes)

- `backend/ai_api/probe.py`: partes puras del sondeo — las cinco series de prueba,
  constructores de URL, lectura de `robots.txt` (grupo del agente, patrón más
  específico, `Allow` gana en empate), detección de desafíos de bot, forma de la
  respuesta, y los parsers de Delcampe (tarjetas), Fesofi (Store API), Iberphil
  (tabla de vendidos, fichas de lote) y el veredicto de una línea.
- `backend/ai_api/management/commands/ai_sources_probe.py`: el comando. Escribe
  `memory-bank/ai-sources-spike.json` y deja los cuerpos fuera del JSON. `--source`
  para una fuente, `--delay` entre peticiones, `--json` para otra ruta.
- `backend/ai_api/test/test_probe.py`: 27 tests sin red ni base de datos.
- `memory-bank/ai-sources-spike.md`: el informe, con los códigos HTTP reales y la
  decisión sobre cada fuente.

Hallazgos que cambian el plan:

1. **Colnect**: la CAPI responde **426** en HTTP/1.1 y **401 `Invalid appId!`** en
   HTTP/2 (`curl`). La red llega; falta la clave. `httpx` está instalado pero **sin
   `h2`**, así que A2 declara `httpx[http2]`. El sitio público devuelve la página
   de **Anubis**: scrapear el catálogo no es opción.
2. **Delcampe**: `robots.txt` prohíbe `/en_GB/collectables/search` (y sus
   equivalentes). La búsqueda funciona con `term=` (con `q` sirve la portada), pero
   **el scraping queda descartado**; A4 sólo por agregador de pago.
3. **Iberphil**: la tabla de vendidos sólo trae la **puja inicial**; el martillo
   está en la ficha y sólo en algunas subastas (la 46 sí, la 47 y la 1 no). Sin
   códigos en las descripciones. Fuente débil, fuera de la primera versión.
4. **Fesofi** (no estaba en el plan): Store API pública `?sku=` exacta con
   `Número EDIFIL`, `Título Serie`, facial, tirada, color, dentado, imprenta y
   fecha. 4 de 5 series resueltas. Es el puente de identidad de A6.
5. **Aviso de datos**: `min(edifil)` y `min(fesofi)` de una serie son sellos
   distintos (Expo 92: Fesofi 3196 ↔ Edifil 3188, con Edifil mínimo 3164). El
   emparejamiento va sello a sello.

### 2026-11-25 — Decisiones del usuario sobre el spike

- **Fesofi sí**: entra como primera fuente de identidad (A6) y como fuente de
  hechos de catálogo. Sin clave y sin coste.
- **Iberphil fuera de la primera versión** (A5 queda escrito pero no se implementa).
- **Delcampe fuera del plan** (A4 eliminado, tampoco por agregador).
- **El precio es orientativo y sale de la media recortada** (sin extremos), no de
  una mediana ni de un único catálogo: `valuation = {estimate, min, max, n,
  method: "trimmed_mean", sources[], as_of}`. Cada observación guarda su `kind`
  (catálogo / oferta / venta), su URL y su fecha, y la mezcla se declara: comparar
  un catálogo de 2020 con una oferta de tienda de hoy da una horquilla, no un
  precio.
- **Sólo sitios permitidos, con la URL guardada.** Fesofi (hechos), TodoColeccion
  (fichas sí; `robots.txt` prohíbe `/buscador`, `?sec=`, `/orientaprecios/`), eBay
  (fichas sí; prohíbe las URLs con `_kw`), Iberphil (permitido, fuera de alcance),
  Delcampe (fuera). **Colnect no se busca: sólo API**, porque su `robots.txt` dice
  que el acceso automatizado sin consentimiento escrito está prohibido.

Quedan tres decisiones abiertas: **la clave de la CAPI de Colnect** (el
procedimiento está en A3; bloquea A3, no A1, A2 ni A6), **el motor que opencode
use por dentro** (ver la entrada siguiente; no bloquea nada) y **dónde se dispara
la investigación** (condiciona A8).

Dos cifras que salen de esta decisión y conviene tener a mano: de los 9.557 sellos,
**2.761 no tienen Edifil y 2.733 de ellos sí tienen Fesofi**, así que Fesofi
recupera el 99% de los códigos que faltaban para poder cruzar con Colnect; y de las
2.541 series, **2.433 ya tienen algún valor** en la base (puesto por el LLM actual,
sin auditoría), que es exactamente lo que A7 tiene que sustituir o marcar.

### 2026-11-25 — Proveedor: opencode (paso A1b)

- **La API usará opencode como proveedor** y **Gemini y Groq se retiran del
  código**: no es un proveedor más entre varios, es el único. Paso nuevo **A1b**,
  con el detalle en §4.
- **No hace falta instalar opencode en el backend.** Se llama a la **API de
  inferencia del Console** (`https://opencode.ai/inference/...`) con
  `Authorization: Bearer oc_sk_…`: HTTP normal, compatible con OpenAI. `opencode
  serve` es otra cosa (servidor local con `OPENCODE_PASSWORD` o emparejamiento) y no
  entra en el diseño.
- **La clave que se crea en el Console es de inferencia**, no autentica clientes de
  `serve`. Para el backend conviene una clave de **service account** (no depende de
  una persona y tiene su propio presupuesto).
- **Los modelos gratuitos del Console sólo funcionan desde dentro de opencode**;
  otros clientes reciben `403` aun con clave. El backend, por tanto, usa modelos de
  pago o Go: se cae la idea de «gratis para el volumen».
- **Una sola familia de API** (OpenAI chat completions) para no mantener tres
  caminos; GPT, Claude y Gemini van por otras familias y necesitarían su rama.
- **El motor se decide más adelante** y no vive en el código: va en el cuerpo de la
  petición (`OPENCODE_MODEL`). Hay 40 modelos bajo el proveedor `opencode`; la
  elección se hará con una tubería que ejecutar, comparando campos inventados,
  huecos declarados, JSON válido y prosa.
- **Serper se queda de momento.** `SERPER_*` y `SearchService` no se tocan; A2 le
  arregla el timeout que hoy no tiene. Si la búsqueda de precios acaba sin
  necesitarlo, se quita en un paso aparte y con su propia nota.
- **Lo que este cambio no arregla**: por esta vía el modelo es una completación sin
  herramientas y puede inventar igual que Gemini. La diferencia la hacen las fuentes
  (A2/A3/A6), no el proveedor.
- Superficie a tocar cuando se implemente, ya localizada:
  `ai_api/services/gemini_provider.py` y `groq_provider.py` (se borran),
  `provider_factory.py` (registro y `LLM_PROVIDER` por defecto),
  `_backend/settings.py` líneas 42–50 (`GEMINI_*`, `GROQ_*`, `LLM_PROVIDER`),
  `.env.example` líneas 19–34, `ai_api/test/test_gemini_provider.py`,
  `test_groq_provider.py`, `test_provider_factory.py`,
  `test_llm_service_facade.py` y `validate_multi_provider_implementation.py`.

### 2026-11-25 — A1 hecho (contrato y modelo de observaciones)

- `backend/ai_api/models.py`: `SourceObservation` con `source`, `external_id`,
  `url`, `issue` / `stamp` (dos FK anulables y un `CheckConstraint` de
  exactamente una), `kind` (**cuatro** valores: `catalog`, `ask`, `sold`,
  `auction_hammer`), `price`, `currency`, `condition`, `observed_at`, `raw` y
  `raw_hash` (identidad sin la fecha, `unique`, calculada en `save()`).
- `backend/ai_api/api/serializers/observation_serializer.py`: `Observation`,
  `SourceReport`, `Gap` y `Valuation` (`estimate`, `min`, `max`, `currency`,
  `sample_size`, `method`, `sources`, `as_of`).
- `series_extraction_response_serializer.py`: bloques nuevos con defaults,
  `description_source` (`llm` por defecto, también en cada sello) y los
  `market_value_*` marcados como obsoletos; el endpoint los pone a `null` aunque
  el proveedor escriba algo.
- `services/prompts.py`: fuera la sección de valuación (la búsqueda imposible y el
  −25 %) y fuera el «EXPANSION» con conocimiento interno; el texto se escribe sólo
  con lo que trae la entrada y `notes` queda vacío si no hay nada que decir.
- 22 tests nuevos (15 de modelo, 7 de contrato), 1.655 verdes, esquema OpenAPI sin
  avisos, migración aplicada y revertida. El detalle está en la ficha del paso, §4.

### 2026-11-25 — A1b hecho (proveedor opencode)

- `ai_api/services/opencode_provider.py`: HTTP contra la API de inferencia del
  Console (`/chat/completions`, `Bearer`), configuración desde `settings`, errores
  con código y cuerpo, `usage` (coste) en el log. Una sola familia de API, la de
  OpenAI.
- `series_extract` **subió a `BaseLLMProvider`**: estaba duplicado en los dos
  proveedores y ahora el flujo vive una vez; el proveedor implementa sólo
  `_single_extract`, `_extract_header` y `_extract_batch`.
- `provider_factory.py` con una sola entrada y **sin `LLM_PROVIDER`**: un valor
  viejo en un `.env` ya no rompe nada (dos tests lo fijan).
- `settings.py`: `OPENCODE_API_KEY`, `OPENCODE_MODEL`, `OPENCODE_BASE_URL`,
  `OPENCODE_TIMEOUT`, `OPENCODE_MAX_TOKENS`; fuera `GEMINI_*`, `GROQ_*` y
  `LLM_PROVIDER`; `LLM_BATCH_SIZE` se queda.
- Borrados los dos proveedores, sus dos tests, `test_batch_processing.py` (sus tests
  del troceado ya estaban en `test_base_llm_provider.py`) y
  `validate_multi_provider_implementation.py`; fuera `google-genai` y `groq` de
  `requirements.base.txt`. `messages.py` ya no nombra `GEMINI_*`, y README y
  docstrings hablan del proveedor único.
- 33 tests en los tres archivos (16 + 8 + 9); **1.628 verdes** (1.655 − 60 tests
  viejos + 33 nuevos), esquema OpenAPI sin avisos.
- **Verificado en real el 2026-11-25**: con `OPENCODE_API_KEY` y
  `OPENCODE_MODEL=glm-5.3-flash`, una extracción desde Swagger pasó la tubería
  entera y devolvió la forma de A1. El paso queda cerrado. El `.env` de cada
  entorno necesita el cambio: fuera `GEMINI_*` / `GROQ_*` / `LLM_PROVIDER`, dentro
  `OPENCODE_API_KEY` y `OPENCODE_MODEL`.
- Lo que se vio al usarlo (tarda, y por qué) está anotado en la ficha de A2 (§4):
  llamadas al modelo en serie, scraping secuencial, el 404 de Serper vacío, la
  lectura muerta de `serie_info` y la falta de tiempos por llamada.


### 2026-11-26 — A2 hecho (capa de fuentes y arreglos)

- `ai_api/sources/`: `http.py` (allowlist, timeouts, reintentos con jitter para
  5xx/429, límite por host, caché TTL, User-Agent, singleton), `errors.py`
  (`SourceError` + `NotAllowed` / `Unavailable` / `NotFound` / `ConfigurationError`),
  `base.py` (`SourceAdapter`) y `registry.py`.
- `SearchService` y `ScrapingService` pasan por el cliente; el scraping va **en
  paralelo** con el límite por host. Medido: la serie de 29 sellos baja de 7,0 s a
  **0,9 s** (0,31 s con caché); la de 6, de 1,7 a 1,2 s.
- El proveedor registra `elapsed_ms` y el `usage`; `ValueError` deja de envolverse,
  así que el 422 de la vista vuelve a existir.
- La vista: allowlist en el atajo de URL (400 si no), `issue_name`/`issue_date`,
  scrape vacío → 422, y 400/404/422/500/502 con significados distintos.
- Defecto 9 cerrado por decisión: la vista sigue siendo master-key only.
- `httpx[http2]==0.28.1` en `requirements.base.txt`; `httpx`/`httpcore` a WARNING en
  `log_setup`; `AI_SOURCE_*` documentadas en `.env.example`.
- 35 tests nuevos; **1.664 verdes**; esquema OpenAPI sin avisos.

### 2026-11-26 — A6 (primera rebanada): encontrar la serie por nombre parcial

- `ai_api/sources/fesofi.py`: `FesofiCatalogue` busca por atributo (`Título Serie`
  y `Año de Emisión`) en la Store API, sin buscador web. Palabras sin acentos ni
  stopwords, el año separado, candidatos probados en orden de cobertura hasta que
  uno tenga productos.
- `SearchService.find_series_url` es ahora un localizador: catálogo primero, Serper
  de respaldo; un fallo del catálogo se registra y se cae al fallback.
- Real: `navidad 1986` → 2884/2883 (Edifil 2867 y 2868), y el scrape de 2884 da la
  serie completa (`Navidad`, 16 noviembre 1986, 2 sellos con sus códigos).
  `castillos de españa 2007` → 4605 (el término de 2007 es «Castillos»).
- **Bug de la caché de A2, encontrado aquí**: la clave era la URL sin la query, así
  que todas las consultas a `/products` compartían entrada. Corregido con test.
- 25 tests nuevos (`test_fesofi.py` 17, `test_search_service.py` 7, uno de caché);
  **1.689 verdes**.
- A6 sigue **abierta**: leer los hechos del producto de la Store API (en vez del
  HTML), el matcher con `score` y los `gaps`. `quijote 1998` ya resuelve (3601) por
  motivo; falta comprobar que es el sello y no una hoja.
- 25 tests de Fesofi y del localizador (`test_fesofi.py` 17, `test_search_service.py`
  7, uno de caché); **1.689 verdes**.

### 2026-11-26 — La descripción deja de cortarse a 180 caracteres

- Visto al usar el endpoint: las descripciones de los sellos salían con
  «…(texto truncado en la fuente)». No era el modelo: `clean_scraped_data` hacía
  `descripcion[:180] + "..."` «para ahorrar ~70 % de tokens», y el `"..."` se añadía
  **siempre**, incluso a textos cortos, así que el modelo creía que todo estaba
  cortado.
- Ahora `DESCRIPTION_LIMIT = 2000` y `_snippet()` corta **sólo** cuando el texto no
  cabe, y entonces lo marca con `…`. Con el catálogo real, las dos fichas de
  Navidad 1986 llegan enteras: 1.223 y 728 caracteres.
- El ahorro que se pierde es una fracción de céntimo: 57 sellos × ~300 tokens extra
  son ~17k tokens, y a los precios del modelo elegido son menos de un céntimo. Lo
  que se ganaba era perder justo el material con el que se escribe la ficha.
- 4 tests nuevos; **1.693 verdes**.
