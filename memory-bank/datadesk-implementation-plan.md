# DataDesk — plan de implementación por pasos

Documento de trabajo. El diseño funcional sigue en
`memory-bank/datadesk-app-plan.md`; esto es **cómo se construye**, cortado en pasos
que se pueden coger y terminar de uno en uno.

Cada paso declara de qué depende. Las dependencias no son un orden estricto: los
pasos sin aristas entre sí se pueden hacer en cualquier orden, en paralelo, o
saltarse temporalmente.

**Estado de implementación: ver §7 al final.** Ahí está qué pasos están hechos,
con fecha, qué ficheros se tocaron y qué se decidió sobre la marcha. Si vienes de
un rebuild del contenedor, lee esa sección antes que nada.

---

## 1. Supuestos (elegidos por defecto, se cambian en D0)

| Tema | Elegido | Por qué |
|---|---|---|
| Traducciones | Comando propio `datadesk_make_messages` con `polib` (Python puro) | No hay `gettext` en ningún Dockerfile y no quiero tocar las imágenes |
| Cuenta | Usuario dedicado `datadesk` con `is_staff=True`, `is_superuser=False` | Un bug en DataDesk no puede tocar Users, APIKey ni Collections |
| Libs JS | Descargadas una vez a `backend/datadesk/static/datadesk/vendor/` y versionadas | Sin npm, sin CDN |
| Caché de throttling | `FileBasedCache` (`CACHES["default"]`) | Producción corre `gunicorn --workers 4` y LocMem daría 5 intentos **por worker**; FileBased los comparte sin tabla ni migración, y con un solo actor no importa que se pierda al recrear el contenedor |
| Despliegue | Local sin nginx · servidor con nginx + TLS | Todo lo que depende de TLS va detrás de `DATADESK_TLS`, sin ramas de código: mismo binario en los dos sitios |
| Herencia sello → serie | **Solo lectura, sin columnas nuevas** (opción A de §2) | País, artista e impresor son de serie por definición y un sello pertenece a una única serie |
| Transporte | Vistas Django que devuelven JSON, **no una API REST** | Sin capa DRF de exposición, sin `/api/v1/`, sin versionado. Sesión + CSRF + `is_staff`; los serializers de DRF solo validan |
| Alcance | Solo `Issue`, `Stamp` y **8 lookups** (`ConditionType` queda en el admin) | Igual que §6 del diseño: existen 9 tablas de lookup, 8 entran en DataDesk |
| Volumen actual | **2.540 series · 9.558 sellos** (≈3,8 de media, **máximo 57** medido en S9) con dispersión amplia: desde 1 sello | El grid del workbench pagina server-side; el de sellos del workspace **no pagina**, porque es siempre una sola serie. No se asume techo: si mañana aparece una serie de 100, debe seguir funcionando sin rediseño |

---

## 2. Corrección de esquema — **cerrada: opción A**

Revisando `stamps_api/models.py`, la lista de "campos heredados" del diseño §3.2
no era exacta:

`Stamp` **no tiene** `country`, `year`, `stamp_type`, `print_type`, `printer`,
`artist`, `paper_type` ni `perforation`. Solo tiene:

```
issue (FK) · edifil_code · fesofi_code · face_value · name · description
image · colors (M2M) · market_value_mnh · market_value_used · total_printed
```

Confirmado también fuera del modelo: `StampRequestSerializer` expone exactamente
esos campos, `StampForm` edita 9 y son los mismos, y ningún sitio del backend
(incluido `ai_api`) escribe esos 8 campos a nivel de sello.

**Decisión (confirmada por el usuario)**: país, artista e impresor son atributos
de la serie, todos los sellos de una serie los comparten, y un sello pertenece a
una única serie. No hay excepciones que registrar → **no se añaden columnas a
`Stamp`**. No hace falta la convención `NULL = hereda` ni el concepto de
override para esos campos.

Consecuencias, que ya están incorporadas a los pasos:

1. **La herencia de esos 8 campos es solo de presentación**: se muestran una vez,
   en la franja de metadatos de la serie (S10), nunca repetidos por fila.
2. **No hay herencia de valores** (decidido 2026-11-18, sustituye al diseño de
   gris/`↺`): lo que la serie guarda describe el **conjunto** —la tirada es la
   de la serie entera y el valor de mercado es lo que vale el conjunto completo,
   normalmente **menos** que la suma de sus sellos— y lo que guarda el sello
   describe el sello. Un número igual es coincidencia, nunca una copia; `name`
   tampoco se hereda. Lo único que se rellena al crear filas es el nombre, porque
   la columna es obligatoria: es un valor por defecto, no una herencia.
3. `face_value` y `name` son **obligatorios** (`NOT NULL`, sin `blank=True`).
   Generar `rows=N` en blanco no vale: cada fila nueva nace con
   `name = <nombre de la serie>` y `face_value` vacío pero marcado requerido.
4. Los tests corren con **SQLite en memoria** (`RUNNING_TESTS=True` en
   `pytest.ini`), así que el servicio **no puede usar nada exclusivo de
   Postgres** (`ArrayField`, `SearchVector`, `distinct on`) o los tests no pasan.
5. Si algún día apareciera una excepción real (un valor impreso por otra
   imprenta), añadir la columna es una migración aditiva barata en Postgres. No
   hay mapa de herencia que mantener: el buffer de S14 compara el valor de cada
   campo con el que traía la fila al abrirla.

Pendiente fuera de este plan: el diseño `memory-bank/datadesk-app-plan.md` §3.2 y
el mockup ya están corregidos con esta decisión.

---

## 3. Mapa de pasos

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| D0 | Decisiones | — | XS | no | — |
| S1 | Esqueleto de app + flag + montaje | — | S | 404/200 | ✅ 2026-11-18 |
| S2 | Estáticos vendorizados + `base.html` | S1 | S | no | ✅ 2026-11-18 |
| S3 | Login, logout, gate, throttling | S1, S2 | M | sí | ✅ 2026-11-18 |
| S4 | i18n en/es + compilador `.po` | S1, S2 | M | sí | ✅ 2026-11-18 |
| S5 | `updated_at` en Issue/Stamp | S1 | XS | no | ✅ 2026-11-18 |
| S6 | `DataDeskChange` + escritor de auditoría | S1 | S | no | ✅ 2026-11-18 |
| S7 | Registry de lookups + `issue_queryset()` + informes | S1 | M | no | ✅ 2026-11-18 |
| S8 | Workbench de solo lectura (JSON + Tabulator) | S2, S3, S7 | L | **sí, primer hito** | ✅ 2026-11-18 |
| S9 | Prueba de rendimiento + índices | S8 | S | no | ✅ 2026-11-18 |
| S10 | Workspace `mode=edit` de solo lectura | S8 | M | sí | ✅ 2026-11-18 |
| S11 | Workspace `mode=new` en seco (sin guardar) | S10 | M | sí | ✅ 2026-11-19 |
| S12 | Núcleo de escritura: `issues/create` + `apply` | S6, S7 | L | no (solo tests) | ✅ 2026-11-19 |
| S13 | Commit de una fila desde el grid | S10, S12 | M | **sí, segundo hito** | ✅ 2026-11-19 |
| S14 | Change set en cliente + footer + undo | S13 | L | sí | ✅ 2026-11-19 |
| S15 | Panel de revisión + commit por lotes | S14 | M | sí | — |
| S16 | `mode=new` completo (auto-numeración, fast row, bucle) | S11, S14 | L | **sí, tercer hito** | — |
| S17 | Clonar serie + borrar con preview de dependencias | S12 | M | sí | — |
| S18 | Crear lookup desde la celda | S12, S14 | M | sí | — |
| S19 | Pantalla de lookups + merge | S7, S12 | M | sí | — |
| S20 | Dashboard + colas "needs attention" | S8 | S | sí | — |
| S21 | Activity log + revertir commit | S6, S12 | M | sí | — |
| S22 | Teclado, i18n final, tests, limpieza | todas | M | sí | — |

Leyenda de tamaño: XS < 1h · S ≈ medio día · M ≈ 1 día · L ≈ 2–3 días.

Hitos entregables: **S8** (ves tus datos), **S13** (puedes corregir un dato),
**S16** (puedes crear una serie), **S19+S21** (mantenimiento completo con red).

---

## 4. Detalle de cada paso

### D0 — Decisiones

Sin código. Cerrar:

1. `polib` vs `gettext` en la imagen vs commitear `.mo`.
2. Usuario dedicado `datadesk` vs superusuario existente.
3. Descargar libs ahora vs que las dejes tú.
4. Dominio real del servidor desplegado (solo para `ALLOWED_HOSTS` /
   `CSRF_TRUSTED_ORIGINS` en el despliegue; en local no hace falta).

(La pregunta de overrides por sello ya está cerrada en §2: opción A, sin
columnas nuevas.)

Salida: nada escrito. Si no hay respuesta, se implementa con los valores de §1 y
se anota en el propio código para revertir fácil.

---

### S1 — Esqueleto de app, flag y montaje

**Depende de**: nada.

- `backend/datadesk/__init__.py`, `apps.py` (`DataDeskConfig`), `urls.py` con
  `app_name = "datadesk"`, `views/dashboard.py` con un `TemplateView` provisional.
- `backend/_backend/settings.py`:
  - `DATADESK_ENABLED = os.getenv("DATADESK_ENABLED", "False")...`
  - `"datadesk"` en `INSTALLED_APPS`
  - `DATADESK_URL = "datadesk/"`, `DATADESK_LOGIN_URL = "/datadesk/login/"`
- `backend/_backend/urls.py`: montar **solo si** `DATADESK_ENABLED`
  (`if settings.DATADESK_ENABLED: urlpatterns += [path(DATADESK_URL, include("datadesk.urls"))]`).
  Nunca dentro de `SERVER_URL_V1`.
- `backend/datadesk/templates/datadesk/dashboard.html`: un `<h1>DataDesk</h1>`.

**Aceptación**: con `DATADESK_ENABLED=False`, `/datadesk/` da 404; con `True`, 200.
`python manage.py check` limpio. `/api/v1/` y el schema de DRF no cambian
(`manage.py spectacular --validate` sin diffs).

**Riesgo**: ninguno. Si algo falla aquí, el resto no empieza.

---

### S2 — Estáticos vendorizados y plantilla base

**Depende de**: S1.

- `backend/datadesk/static/datadesk/vendor/`: `htmx.min.js` (2.x),
  `alpine.min.js` (3.x), `tabulator.min.js` + `tabulator.min.css` (6.x).
  Comprobar licencias y fijar versión exacta en un `VERSIONS.md` al lado.
- `backend/datadesk/static/datadesk/datadesk.css`: tokens del mockup (colores,
  densidad del grid, barra de commit).
- `backend/datadesk/templates/datadesk/base.html`: topbar, barra de idioma,
  bloque de contenido, `{% block extra_js %}`, `hx-headers` con CSRF.
- `dashboard.html` pasa a extender `base.html`.

**Aceptación**: `manage.py collectstatic --noinput` funciona con
`CompressedManifestStaticFilesStorage` (whitenoise ya está configurado) y la
página carga los 4 ficheros con `{% static %}`. En `DEBUG=True`, 200 en cada
asset.

**Riesgo**: el manifest storage rompe si algún template referencia un fichero
inexistente. Se detecta en `collectstatic`, no en runtime.

---

### S3 — Autenticación, gate y throttling

**Depende de**: S1, S2.

- `datadesk/views/auth.py`:
  - `DataDeskLoginView(LoginView)` → `template_name="datadesk/login.html"`,
    `redirect_authenticated_user=True`, `next_page` a `/datadesk/`. **Obligatorio**:
    `LOGIN_REDIRECT_URL` no está definido en settings, y sin `next_page` Django
    manda a `/accounts/profile/`.
  - Throttling dentro de `form_invalid()`: clave
    `datadesk:login:{username}:{ip}`, 5 fallos / 5 min → 429 con `Retry-After`
    (el contador se limpia en `form_valid()`).
  - `CACHES["default"]` = `FileBasedCache` en `LOCATION = BASE_DIR / ".cache"`,
    compartida por los 4 workers y con `.cache/` añadido a `.gitignore`. Sin
    `createcachetable`, sin migración. LocMem queda descartado porque
    multiplicaría el límite por worker.
  - Clave por IP: se usa `REMOTE_ADDR` a secas. **Detrás de nginx esa IP es la del
    proxy**, así que la clave colapsa a una sola: en la práctica el throttling
    pasa a ser por usuario, que es justo lo que se quiere con un solo actor. No
    hace falta `real_ip_header` ni leer `X-Forwarded-For` en Django.
  - `DataDeskLogoutView(LogoutView)`: en Django 6 ya es POST-only, no hace falta
    nada; solo plantilla/redirect.
  - `datadesk/views/partials/login_form.html` para poder devolver 429 por HTMX.
- `datadesk/mixins.py`: `DataDeskAccessMixin(LoginRequiredMixin, UserPassesTestMixin)`
  con `login_url="/datadesk/login/"`, `test_func = user.is_active and user.is_staff`
  y `raise_exception` para peticiones JSON (401/403 en vez de redirect HTML).
  **No** se toca el `LOGIN_URL` global de settings: el admin ya tiene su propia
  vista de login y DRF su `LOGIN_URL_V1`, así que cambiarlo solo añade riesgo.
- `datadesk/middleware.py`: `DataDeskGateMiddleware` — para todo path bajo
  `/datadesk/` que no sea login/logout, exige `is_staff`. Es el cinturón para los
  endpoints JSON que se olviden del mixin.
- `settings.py`: `MIDDLEWARE += ["datadesk.middleware.DataDeskGateMiddleware"]`
  (después de `AuthenticationMiddleware`), `SESSION_COOKIE_AGE = 14 días`,
  `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE="Lax"`.

  Todo lo de TLS va condicionado a `DATADESK_TLS`, para que el mismo código corra
  en local y en el servidor:
  - `DATADESK_TLS=0` (local, `runserver`, sin nginx): cookies sin `Secure`,
    sin `SECURE_PROXY_SSL_HEADER`. Login por HTTP en `localhost`.
  - `DATADESK_TLS=1` (servidor, nginx delante): `SESSION_COOKIE_SECURE`,
    `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`.
    `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` ya se leen de entorno, así que no se
    tocan: solo hay que rellenarlos en el despliegue.

- `datadesk/templates/datadesk/login.html`: usuario, contraseña, error, `next`.
- Comando de alta documentado en README:
  `manage.py createsuperuser` o `shell` para crear `datadesk` staff no-superuser.

**Aceptación** (`datadesk/tests/test_auth.py`, Django test client):
- anónimo en `/datadesk/` → 302 a `/datadesk/login/?next=/datadesk/`
- usuario no-staff → 403
- staff → 200
- `GET /datadesk/logout/` → 405; `POST` → 302 y sesión cerrada
- 6 fallos seguidos → 429; el contador caduca a los 5 min (congelando caché)
- login correcto limpia el contador
- con `override_settings(DATADESK_TLS=True)` las cookies salen `Secure` y el
  header del proxy queda configurado; con `False` no, y el login funciona por
  HTTP sin nginx (que es el caso local)
- el throttling funciona con la caché de fichero, no con LocMem: un test que
  simula dos workers leyendo la misma entrada

**Riesgo**: que lo probado en local no sea lo que corre en el servidor. Se evita
no teniendo dos caminos de código: `DATADESK_TLS` solo cambia flags de cookies y
un header, nunca lógica. El segundo riesgo es la IP del proxy (ver arriba): con
nginx la clave de throttling colapsa, y eso es aceptable aquí.

**Allowlist por IP**: queda **solo documentada** en el README, no implementada.
Se añadirá cuando DataDesk esté terminado, como receta de nginx
(`allow <ip>; deny all;` sobre `/datadesk/`), no como código de la app.

---

### S4 — i18n en/es

**Depende de**: S1, S2.

- `backend/datadesk/locale/{en,es}/LC_MESSAGES/django.po`.
- `datadesk/management/commands/datadesk_make_messages.py`: recorre los `.po` y
  escribe `.mo` con `polib` (añadir `polib` a `requirements.base.txt`).
  Opciones `--check` para CI (falla si `.po` cambió y `.mo` está viejo).
- `settings.py`: `LANGUAGE_CODE` se queda como está; añadir
  `LocaleMiddleware` **solo si** no está ya (comprobar) y
  `DATADESK_LANGUAGES = ("en", "es")`.
- Selector EN/ES en `base.html` → `POST /datadesk/language/` que hace
  `set_language` y vuelve al `next`. Nunca toca `assets/locales/*.json`.

**Aceptación**: `datadesk_make_messages` genera `.mo` sin `gettext`; cambiar a ES
traduce el dashboard y sobrevive a la recarga; el test comprueba que
`assets/locales/en.json` y `es.json` siguen intactos (`git status` limpio).

**Riesgo**: `polib` es una dependencia nueva en la imagen de producción (pura
Python, ~50KB). Alternativa si molesta: commitear los `.mo`.

---

### S5 — Timestamps

**Depende de**: S1.

- `Issue.updated_at`, `Stamp.updated_at`: `DateTimeField(auto_now=True, db_index=True)`.
- Migración limpia (la BD está al día, no hay backfill).
- `__str__`/admin no cambian.

**Aceptación**: migración aplica y revierte; un `save()` actualiza el campo;
`updated_at` aparece en el admin como `readonly`.

**Nota**: `db_index=True` en dos columnas de una tabla con pocos miles de filas
es barato. Si S9 muestra que no se usa para ordenar, se puede quitar.

**No hay más cambios de esquema** en todo el plan: `Stamp` no gana los 8 campos
de serie (§2, opción A).

---

### S6 — Auditoría

**Depende de**: S1 (y S5 por comodidad).

- `datadesk/models.py`: `DataDeskChange` tal cual el diseño §5 (`commit_id` UUID,
  `user` FK `SET_NULL`, `model_label`, `object_id`, `operation`, `before`,
  `after`, `created_at`), más dos columnas nullable que necesita S21:
  - `reverted_at` en las filas originales → un commit solo se puede revertir una
    vez, y el motivo se ve en el log.
  - `reverts_commit_id` en las filas del revert → enlaza el revert con el commit
    que deshace, sin parsear JSON.
- `datadesk/audit.py`: `snapshot(instance) -> dict` (solo campos editables,
  `Decimal`/`date` serializados, FKs como ids y `colors` como lista de ids) y
  `record(commit_id, user, instance, op, before, after)`.
- `operation` admite `create|update|delete|merge`.
- Admin mínimo **de solo lectura** para consultarlo desde `/admin/` mientras no
  exista S21 (no permitir add/change/delete).

**Aceptación**: test unitario de `snapshot()` con `Decimal`, `date`, FK y M2M
(`colors` como lista de ids); `record()` agrupa por `commit_id`; el revert de
S21 puede recrear un `Stamp` a partir del snapshot sin consultar otra tabla.

---

### S7 — Registry de lookups y querysets

**Depende de**: S1.

- `datadesk/registry.py`:

```python
LOOKUPS = {
  "year":        {"model": Year,        "label": _("Year"),        "numeric": True,  "refs": [("issues_api.Issue", "year")]},
  "country":     {"model": Country,     ...},
  "color":       {"model": Color,       ...},   # refs vía Stamp.colors
  "artist":      ..., "printer": ..., "paper_type": ...,
  "print_type":  ..., "stamp_type": ...,
}
```

Cada entrada sabe: modelo, `verbose_name`, si es numérico, y las relaciones que
apuntan a ella (para S19: contadores de uso y merge).

- `datadesk/service.py` (esqueleto):
  - `issue_queryset()` con `select_related` de los 7 FK y
    `annotate(stamp_count=Count("stamps"))`
  - `stamp_queryset(issue_id)` con `prefetch_related("colors")`
  - `missing_data_report()` → dict de contadores (sin país, sin fecha, sin
    sellos, sellos sin color, sellos sin face_value, sin imagen)
- `datadesk/tests/test_service_read.py` con datos mínimos por fixture.

**Aceptación**: `issue_queryset()` hace **una** query para la lista (comprobado
con `assertNumQueries`), y `missing_data_report()` devuelve los 6 contadores
correctos sobre un dataset pequeño.

**Riesgo**: `Count` + `prefetch` mal combinados duplican filas; el test de
`assertNumQueries` lo caza.

---

### S8 — Workbench de solo lectura  ← primer hito

**Depende de**: S2, S3, S7.

- `GET /datadesk/grid/issues`: JSON para Tabulator con
  `page`, `size`, `sort[]`, `filter[]` → `year_min/max`, `q` (nombre),
  `country`, `stamp_type`, `attention`.
  Devuelve `last_page`, `data[]`, `total`.
- `GET /datadesk/issues/` → página con filtros (rango de años, buscador,
  país, tipo, selector "needs attention") persistidos en URL y `localStorage`.
  Delay de 300 ms en el buscador, igual que el frontend actual.
- **Columnas visibles por defecto**: `year · date · name · country ·
  stamp_type · printer · stamps · mnh · used`. Detrás de un toggle: `print_type ·
  artist · paper_type · perforation · total_printed · badge de huecos`. La
  elección se persiste con los filtros; 14 columnas fijas no caben legibles a
  1366px.
- **Badge de huecos por fila**: icono compacto con marcas (`◦` sin país, `◦` sin
  fecha, `◦` sin sellos), calculado en la misma query que filtra — los `Exists`
  ya están ahí, mostrarlo no cuesta nada. Es la señal que convierte la tabla en
  una cola de trabajo.
- Orden por columna, agrupación por año, paginación server-side.
- Todo el JS en `datadesk/static/datadesk/workbench.js`, sin lógica inline.

**Aceptación**: abre con las **2.540 series y 9.555 sellos** reales, primera
página (100 filas) en menos de 300 ms en local y scroll fluido; los filtros y la
selección de columnas sobreviven a recargar (URL); un `?attention=no_stamps`
devuelve solo las series sin sellos; el badge marca lo mismo que ese filtro.
`pytest` cubre el endpoint: paginación, orden, cada filtro y el caso sin
resultados.

**Riesgo**: es el paso más grande y el que decide si el resto tiene sentido.
Con este volumen (≈10k sellos en total) el cliente **podría** cargar todo de una
vez —unos cientos de KB—, pero se mantiene server-side: el día que la BD crezca
diez veces no hay que rehacer el grid, y el coste es un endpoint con seis
parámetros. Si Tabulator no rinde (poco probable a 2.540 filas), la alternativa
es paging puro con HTMX y el plan cambia en S14–S16.

---

### S9 — Rendimiento e índices

**Depende de**: S8.

- Medir con el dataset real (**2.540 series / 9.555 sellos**): primera página,
  última página (el `OFFSET` grande es el caso peor), filtro por año, búsqueda
  de texto, cada cola de "needs attention" y la carga de la **serie más larga**
  en el workspace. `EXPLAIN ANALYZE` de las dos primeras.
- A 2.540 filas un seq scan de `Issue` es milisegundos: **no añadir índices por
  reflejo**. Solo si el plan los pide (`Issue.name`/`unaccent` para búsqueda,
  `(year_id, date)` para el orden por defecto), y comprobando que el planner los
  usa de verdad.
- Dejar los números escritos en `memory-bank/datadesk-perf.md` para comparar
  después de S14.

**Aceptación**: p95 < 300 ms en las cinco consultas medidas, ninguna query por
fila (contador constante al cambiar `size`), y el `OFFSET` de la última página
no se degrada respecto a la primera.

---

### S10 — Workspace `mode=edit` (lectura)

**Depende de**: S8.

- `GET /datadesk/issues/<id>/` → `datadesk/issue_workspace.html`, contexto con
  `mode="edit"`, la serie y sus sellos.
- Cabecera de metadatos en solo lectura (los 14 campos del mockup), fechas y
  decimales formateados según idioma.
- Grid de sellos con Tabulator en modo lectura: `edifil`, `fesofi`, `name`,
  `face_value`, `colors`, `mnh`, `used`, `total_printed`, `img` (indicador).
  Solo campos del sello: los 8 atributos de serie **no se repiten por fila**.
- **Sin herencia**: los 8 campos de serie (`country`, `year`, `stamp_type`,
  `print_type`, `printer`, `artist`, `paper_type`, `perforation`) viven solo en
  la franja superior fija (§2) y el grid muestra únicamente valores del sello.
  No hay gris heredado, ni `⟲`, ni mapa `inherited`: lo de la serie describe el
  conjunto (tirada, valor del conjunto) y lo del sello, el sello.
- Enlace "abrir" desde cada fila del workbench y `Enter`.

**Aceptación**: una serie de 8 sellos carga con 1–2 queries; los grises
coinciden con el mockup; `Esc` vuelve al workbench conservando filtros. Se
prueba además con la **serie más larga real (57 sellos, medido en S9)**, que debe
seguir pintándose sin paginar, y con un fixture de 100 para confirmar que no hay
ningún límite duro escondido en la plantilla ni en el queryset.

---

### S11 — `mode=new` en seco

**Depende de**: S10.

- `GET /datadesk/issues/new/` → **misma plantilla**, `mode="new"`, sellos vacíos.
  La ruta va antes de `issues/<int:pk>/` y usa convertidor `int:` en el detalle,
  así que `new` nunca compite con un id ni un id inválido abre una serie.
- La franja de metadatos se convierte en **formulario editable** con los 15 campos
  de `Issue`; en `edit` la franja sigue siendo de solo lectura. El formulario no
  se envía: todavía no existe endpoint de escritura.
- **Prefill solo de `country` y `year`** desde la última serie
  (`Issue.objects.order_by("-id").first()`, 1 query). El botón `↺ Use last issue`
  los reaplica **sin recargar**: los valores viajan en la configuración de la
  página. El resto no se copia, por probabilidad de repetición y por daño:

  | Campo | Se prefija | Por qué |
  | --- | --- | --- |
  | `country` | sí | casi constante; si cambia, se ve en la primera celda |
  | `year` | sí | la entrada es secuencial por año y es el contexto de la pantalla |
  | `stamp_type`, `print_type`, `printer`, `artist`, `paper_type`, `perforation` | no | cambian por serie; copiarlos obliga a limpiarlos |
  | `date`, `name` | no | identifican la serie; la fecha heredada es el error más caro |
  | `description`, `note` | no | texto libre que acabaría describiendo otra serie |
  | `total_printed`, `market_value_mnh`, `market_value_used` | no | son del conjunto: copiarlos corrompe datos |

  Sin series en la BD no hay prefill y el botón se **oculta** (no se deshabilita:
  un botón muerto invita a pulsarlo).
- El **año no es un desplegable**: un `input[type=number]` con los años existentes
  como `<datalist>`, porque una serie casi siempre inaugura año y un `select` no
  puede expresar uno que todavía no tiene fila. El valor viaja como **número, no
  como id**, y al guardar se resuelve con `get_or_create` igual que el resto de
  lookups creados en línea (S12). Rango 1800–año actual+2 contra erratas, y un
  aviso silencioso «se creará al guardar» cuando el número tecleado no está en la
  lista de sugerencias.
- El workbench gana un enlace `+ New series` a la derecha de la barra: sin él la
  pantalla solo se abre escribiendo la URL. El bucle «Create another» y los
  atajos siguen en S16.
- Control `rows=N`: **1–100, por defecto 4** (la media real es 3,8 sellos por
  serie), y S16 no lo cambia. Genera filas **en cliente**, sin petición de red y
  sin fila en la BD. Cambiar `N` **solo añade o quita filas vacías por el final**;
  nunca reescribe una fila tocada ni borra por debajo de ellas.
- Cada fila nueva nace con `name = <nombre de la serie>` (la columna es NOT NULL)
  y `face_value` vacío pero requerido. Nace `touched: false`, y su nombre **sigue
  al de la serie** mientras nadie la toque; el primer keystroke o color la marca y
  deja de seguir. Ese flag es la línea base que S14 comparará campo a campo.
- Identidad de fila `new-1`, `new-2`…: los ids reales son números, así que el
  prefijo no puede colisionar con ellos; lo manda el servidor en la configuración
  y nunca se reutiliza un número al borrar una fila.
- `Shift+Enter` no hace nada y el aviso «todavía no guarda» está **visible bajo el
  pie de la pantalla**, no en un tooltip (un atajo deshabilitado no recibe hover).
- `beforeunload` solo con la pantalla **sucia**: algún campo distinto del
  prefijado, o filas añadidas/quitadas. Sin borradores: recargar descarta.

**Aceptación**: alternar `new`/`edit` no rompe nada; el prefill es el de la
última serie real y solo `country`+`year`; en `new` no aparece `Clone`/`Delete` y
sí `Use last issue`; el año se teclea, admite uno que todavía no tiene fila (con
su aviso) y el rango descarta lo que no es un año; `rows=N` genera exactamente N
filas sin red y sin BD; bajar `N` no toca filas marcadas; **recargar o salir
descarta el borrador** (no hay recuperación posible en `new`, por decisión) y el
`beforeunload` avisa antes de perderlo.

---

### S12 — Núcleo de escritura

**Depende de**: S6, S7.

Paso **sin interfaz**: se construye y se prueba solo con pytest. Así S13, S17,
S18 y S19 pueden empezar sin esperarse entre sí.

**Transporte**: vistas Django normales bajo `/datadesk/` que devuelven JSON. No es
una API REST ni una capa DRF de exposición: sesión + CSRF + `DataDeskAccessMixin`,
y los serializers de DRF se usan **solo para validar**. Nada nuevo bajo
`/api/v1/`.

Dos caminos, una transacción cada uno:

- `POST /datadesk/issues/create` — `{issue: {...}, stamps: [{...}, ...]}` →
  **todo o nada**. Sin ids temporales: los sellos van anidados y el servidor pone
  el `issue_id`. Si un sello no valida, no se crea la serie.
- `POST /datadesk/apply` — `{changes: [{model, object_id, op, patch,
  expected_updated_at?}]}` → **savepoint por fila**: los válidos se aplican y los
  rechazados vuelven como `{index, errors}` al buffer. Solo `create`/`update`;
  **`delete` no se acepta aquí** (va por S17, con preview de dependencias).

Comparten `_validate_row()` (`IssueRequestSerializer` /
`StampRequestSerializer` en `partial=True`), el escritor de auditoría de S6 y el
tope de 500 cambios por petición.

Decisiones cerradas con el usuario:

- **Sin ids temporales**: por eso crear serie tiene endpoint propio en vez de un
  `apply` genérico. El 90% de los commits son "una serie con sus sellos" o "N
  filas de una serie existente"; no compensa la maquinaria de referencias
  pendientes.
- **Borrado fuera de `/apply`**: si llega un `delete`, se responde 409 con
  `{needs_confirmation: true}` y no se aplica nada. Cualquier bug del cliente no
  puede borrar una serie de 24 sellos y sus `CollectionItem` sin preview.
- **Fallo parcial**: `/issues/create` es todo o nada (un lote a medias dejaría
  media serie); `/apply` mantiene savepoint por fila, que es lo correcto para 40
  correcciones heterogéneas.
- Lookups creadas desde una celda: `get_or_create` → `{id, name, created: bool}`;
  un nombre duplicado devuelve el existente en vez de un 500.
- `colors`: `.set()` en bloque dentro de la transacción, nunca fuera.
- `expected_updated_at` opcional por fila: si no coincide, esa fila se rechaza
  con "modificado en otra pestaña"; el resto se aplica.
- Un `commit_id` por petición, devuelto al cliente y usado en todos los
  `DataDeskChange`. Los rechazos no escriben auditoría; los aplicados sí.

**Aceptación** (`datadesk/tests/test_service_write.py`):
- create: serie + 8 sellos + colores + 8 filas de auditoría con el mismo
  `commit_id`; un sello inválido → 0 filas creadas y 0 `DataDeskChange`
- apply: 40 cambios válidos → 40 aplicados, 40 `DataDeskChange` con un `commit_id`
- un cambio inválido en medio → 39 aplicados y el inválido devuelto con
  `{index, errors}`; la BD queda coherente
- fallo simulado a mitad (`mock` que lanza) → **rollback total**: cero filas y
  cero `DataDeskChange`
- `delete` en `/apply` → 409 y nada aplicado
- `expected_updated_at` viejo → solo esa fila rechazada, el resto aplicado
- más de 500 cambios → 400 antes de tocar la BD
- sin `is_staff` → 403; sin CSRF → 403
- lookup duplicada → devuelve la existente con `created: false`

---

### S13 — Commit de una fila desde el grid  ← segundo hito

**Depende de**: S10, S12.

- Edición inline de celdas en el grid de sellos (Tabulator `editModule`).
- `Shift+Enter` → construye un change set de una fila → `POST /datadesk/apply`.
- Celda optimista + marca de "guardado"; en error, revierte el valor y muestra
  el mensaje del servidor en la fila.
- Los campos de la cabecera de la serie se pueden editar igual, con el mismo
  camino (una fila de `Issue`).

**Aceptación**: cambiar un `edifil_code`, `Shift+Enter`, recargar y verlo
persistido; un valor inválido deja la fila marcada y no pierde el foco; se crea
una fila en `DataDeskChange`.

---

### S14 — Change set en cliente

**Depende de**: S13.

Lo que convierte el grid en un editor de verdad: los cambios dejan de enviarse
solos y se acumulan hasta el commit (S15).

- Estado en Alpine, **una entrada por objeto**, no por celda:

```js
buffer = {
  rows: {
    "stamp:412": { model: "stamp", object_id: 412, op: "update",
                   patch: { edifil_code: "2745" },        // solo lo tocado
                   base:  { edifil_code: "2744" },        // valor de servidor al cargar
                   expected_updated_at: "2026-11-18T09:12:00Z" },
    "stamp:new:3": { model: "stamp", object_id: null, op: "create",
                     issue_id: 98, patch: { ... }, base: {} },
  },
  ops: [],   // pila de undo/redo
}
```

- **Diff contra `base`**: si un campo vuelve al valor original, se borra del
  `patch`; si la entrada se queda sin campos, desaparece del buffer. Así nunca se
  envía un cambio que no cambia nada. Añadir un sello a una serie existente es
  `op: "create"` con `issue_id`; en `mode=new` los sellos viajan en el array
  `stamps` de `/datadesk/issues/create` y no necesitan id temporal.
- **El `base` sale de Tabulator** (`cell.getOldValue()`), no de una copia
  paralela: una sola fuente de verdad evita desincronizaciones cuando el grid se
  reordena o filtra.
- **Colores (M2M) no son un campo más**: el patch lleva `colors: [ids]` y el
  buffer guarda también los nombres para que el panel de revisión pinte
  `Carmín, Rojo` sin consultar al servidor.
- **Undo/redo como log de operaciones**, no como snapshots:
  `{type: "cell", key, field, from, to}` con puntero; deshacer escribe `from`.
  Una edición nueva después de deshacer trunca la pila de redo. Tope de 200
  operaciones. `Ctrl+Z` / `Ctrl+Shift+Z`.
- **Diff contra la fila original**, campo a campo: el buffer guarda `base` y
  `patch` por objeto y una celda cuenta como cambiada solo si su valor difiere
  del que traía la fila. No hay estados "heredado"/"propio" que mantener (ver
  §2): el gris y el `↺` desaparecieron con el diseño de herencia.
- **Persistencia, solo en `mode=edit`**: `localStorage` con clave
  `datadesk:buffer:edit:<issueId>`, escritura *debounced* (400 ms), más
  `schemaVersion` y `savedAt`. Al entrar con un buffer guardado se ofrece
  "recuperar 12 cambios" (nunca auto-restaurar). Se borra al commitear o al
  descartar; una versión de esquema distinta se descarta con aviso.
- **En `mode=new` NO se persiste nada** (decisión del usuario): una serie se
  termina en el momento o se vuelve a empezar, no hay "lo acabo mañana". El
  buffer vive en memoria y muere con la pestaña; `Ctrl+Z` sigue funcionando
  dentro de la sesión. La única red es el `beforeunload`, que aquí es
  imprescindible.
- **Dos pestañas**: `storage` event → banner "otra pestaña tiene cambios en esta
  serie". Aviso, no bloqueo. El chequeo duro es por fila con
  `expected_updated_at` (S12), que rechaza justo las filas pisadas.
- **`beforeunload`** si hay cambios sin guardar. Solo salta en navegación
  completa; los enlaces HTMX internos no lo disparan, así que el botón de volver
  al workbench pide confirmación explícita.
- **Plurales en el footer**: "1 cambio" / "12 cambios" se resuelven con
  `ngettext` en servidor y se inyectan como JSON (§4), para no duplicar reglas de
  plural en JS.

**Lo que NO entra en el buffer: los borrados.** `/datadesk/apply` rechaza
`delete` (S12), así que borrar un sello o una serie es una acción **inmediata**
con su propio diálogo de confirmación (S17) y queda **fuera del undo**: `Ctrl+Z`
no resucita un sello borrado. Se avisa en la UI; el camino de vuelta es el log de
actividad y el backup.

**Aceptación**: 12 cambios acumulados en `edit` sobreviven a un F5 y se ofrecen
al volver; en `new`, recargar descarta el borrador (y avisa antes); volver un
campo a su valor original lo saca del buffer (el contador baja); `Ctrl+Z` deshace
en orden y truncar el redo funciona; el contador cuadra con el panel de S15; dos
pestañas muestran el banner sin bloquear; el commit con una fila tocada en otra
pestaña la rechaza por `expected_updated_at` y mantiene el resto.

---

### S15 — Panel de revisión y commit por lotes

**Depende de**: S14.

- Panel lateral: agrupado por modelo, `antes → después` por campo, contador,
  botón `Commit N changes` (`Ctrl+Enter`) y `Discard`.
- Post a `/datadesk/apply` con el set completo; los rechazados **se quedan** en
  el buffer con su error y los aplicados desaparecen.
- Tras commit en `edit`: volver al workbench con foco en la fila guardada.
- Botón `POST /datadesk/backup` (comando `stamps_db_backup` ya existente) cuando
  el set supera N filas.

**Aceptación**: commit de 40 filas en una sola transacción (contador de queries
y `commit_id` único en BD); rechazo parcial deja 38 aplicados y 2 en el buffer;
el backup se dispara por encima del umbral. Una serie completa entra siempre en
un solo commit: con 24 sellos de techo actual y un límite de 500 cambios por
petición, no hay commits por tramos.

---

### S16 — `mode=new` completo  ← tercer hito

**Depende de**: S11, S14.

- Sin herencia que editar: lo único que se rellena al crear filas es `name`
  (obligatorio) y ya lo hace S11 con el flag `touched`; `↺ Use last issue`
  reaplica `country` y `year`, nunca valores de sellos.
- `Fill series`: numera `edifil` consecutivamente preservando sufijo
  (`2744a → 2744b`); si el primer código no es numérico, no hace nada y avisa.
- `fast row`: solo `edifil`, `fesofi`, `face_value`, `colors` (por defecto ON).
- `rows=N`: por defecto 4, máximo 100. Una serie de un solo sello es `rows=1`,
  sin flujo especial; para series largas `Ctrl+D` y `Fill series` hacen el
  trabajo.
- `Ctrl+D` duplica fila; pegar TSV desde el portapapeles.
- Commit → una transacción `Issue` + N `Stamp` + M2M + auditoría, vía
  `/datadesk/issues/create` y **todo o nada**; después
  `Create another in <year>` con los metadatos cargados (bucle sin salir).
- `Shift+Enter` → crear la serie sola (los sellos no son obligatorios).
- **Sin borradores**: nada de lo tecleado en `new` se guarda en `localStorage`.
  Si se abandona, se empieza de cero; el `beforeunload` es la única red. La única
  excepción es el bucle `Create another in <year>`, que conserva los metadatos
  porque los reenvía el servidor, no el cliente.

**Aceptación**: crear una serie de 8 sellos con 4 columnas de tecleo real,
recargar y ver 8 sellos con colores; el bucle deja la segunda serie a un clic;
`Fill series` probado con sufijos y con códigos no numéricos.

---

### S17 — Clonar y borrar

**Depende de**: S12.

- `POST /datadesk/issues/clone`: copia la serie y sus sellos (con colores), con
  `year`/`date` sobreescribibles, y abre el workspace en `mode=edit` sobre la
  copia.
- Borrado con preview server-side: nº de sellos, nº de `CollectionItem`
  afectados y nº de colecciones de usuario; confirmación escribiendo el año.
- Ambas acciones auditadas (`operation="create"` enlazando el origen en `after`).

**Aceptación**: clonar 8 sellos mantiene colores y `edifil`; borrar una serie
con `CollectionItem` avisa del número exacto y no borra si el texto no coincide;
sin `CollectionItem` el preview lo dice explícitamente. Probado también con la
serie de 24 sellos: el preview cuenta los 24 y la confirmación por año no cambia.

---

### S18 — Crear lookup desde la celda

**Depende de**: S12, S14.

- Autocomplete en las celdas de lookup (`country`, `artist`, `printer`, …) que
  busca en `/datadesk/lookups/<table>/search?q=`.
- Si no existe, opción `+ Crear "X"` que hace `POST` y devuelve `{id, name}`;
  el cambio entra en el change set como `create` de la lookup.
- En `colors` (M2M) lo mismo, multi-selección con chips.

**Aceptación**: crear un artista nuevo desde una celda y verlo en el
autocomplete de otra serie sin recargar; nombre duplicado → error claro, no 500;
el `create` de la lookup aparece en el panel de revisión.

---

### S19 — Pantalla de lookups y merge

**Depende de**: S7, S12.

Existen 9 tablas de lookup; **8 entran en DataDesk** (`ConditionType` se queda en
el admin porque solo la usan las colecciones de usuario). Una sola plantilla
para las 8, sin una vista por tabla.

- `datadesk/registry.py` describe cada lookup sin código repetido:

```python
LOOKUPS = {
  "year":    {"model": Year,    "name_field": "year", "kind": int,
              "reverse": "issues",  "fk_on": ("issues_api.Issue", "year")},
  "color":   {"model": Color,   "name_field": "name", "kind": str, "m2m": ("stamps_api.Stamp", "colors")},
  "artist":  {"model": Artist,  "name_field": "name", "kind": str,
              "reverse": "issues",  "fk_on": ("issues_api.Issue", "artist")},
  ...
}
```

- **Contadores de uso en una sola query**: cada entrada lleva el
  `related_name` inverso (`issues`, `stamps`), así que el grid es
  `Model.objects.annotate(usage=Count(reverse))` paginado. Nunca un `count()`
  por fila.
- **Renombrar** inline con el contador como preview ("usado por 143 sellos").
  Si el nombre nuevo ya existe, `IntegrityError` → **409 con {"error":
  "duplicate_name", "existing_id": id}** y la UI ofrece fusionar, que es lo que
  el usuario quería el 90% de las veces.
- **Fusionar** (`POST /datadesk/lookups/merge`,
  `{table, from_id, to_id, keep_name_from: "a"|"b"}`), en una transacción. El
  diálogo muestra los dos nombres con un selector de **qué nombre se queda**, así
  que el caso "el bueno es el de B" no obliga a renombrar antes:
  - **FKs** (`country`, `artist`, `printer`, `paper_type`, `print_type`,
    `stamp_type`): un `update(fk=to)` — sin instanciar 2.540 objetos — y además
    `.update(updated_at=timezone.now())`, porque `auto_now` **no** se dispara con
    `update()` y sin eso el chequeo de conflicto de S12 se queda ciego.
  - **`colors` (M2M)**: como un sello puede tener los dos colores, se resuelve
    por la tabla intermedia y no con `.set()`: se insertan los pares que faltan
    (`bulk_create(..., ignore_conflicts=True)`) y después se borran las filas del
    color origen. Sin duplicados y sin depender de que `.add()` ignore
    conflictos, que cambió entre versiones de Django.
  - **`year`**: igual que un FK, pero es `CASCADE`; fusionar dos años mueve sus
    series y no borra ninguna.
  - Se borra el origen, y la auditoría es **una fila** `operation="merge"` con
    `before={lookup: B, refs: n}` y `after={lookup: A, refs: m}`, no 143 filas
    de ruido.
  - Si `keep_name_from="b"`, el orden importa y es justo este: mover
    referencias → borrar B (eso libera su nombre, que es `unique`) → renombrar A
    con el nombre de B. Al revés choca contra la constraint. Un `IntegrityError`
    en este último paso revierte la transacción entera y devuelve 409.
  - **Un merge no es reversible** (decisión del usuario): la auditoría guarda el
    recuento, no los ids movidos, así que S21 rechaza revertir cualquier commit
    que contenga un `merge`. La pantalla lo advierte antes de confirmar y el
    backup es la red de seguridad.
- **Borrar** un lookup solo si `usage == 0` (se resalta en el grid); con uso,
  la única vía es fusionar.
- `Year`: acción "crear los próximos 10 años" (`get_or_create` en bucle).

**Aceptación**: fusionar dos artistas mueve exactamente N referencias, deja 0
filas apuntando al origen y borra el origen; fusionar dos colores donde un sello
tiene ambos deja **una** fila en la tabla intermedia y ninguna duplicada;
fusionar años mueve las series; `keep_name_from="b"` deja el nombre de B en el
registro superviviente y no choca con `unique`; renombrar a un nombre existente
devuelve 409 con el id del existente; borrar un lookup con uso devuelve 409; el
contador del grid coincide con el número real de referencias (una query,
comprobado con `assertNumQueries`); todo queda en auditoría, y un commit con
`merge` queda marcado como no reversible y S21 lo rechaza con el motivo.

---

### S20 — Dashboard y colas

**Depende de**: S8.

- `/datadesk/` con los 6 contadores de `missing_data_report()` y enlaces a
  `/datadesk/issues/?attention=...`.
- Añadir "sin imagen" al selector del workbench si S8 no lo incluyó.

**Aceptación**: los números del dashboard coinciden con el recuento del
workbench filtrado; cada tarjeta es un enlace directo.

---

### S21 — Activity y revertir

**Depende de**: S6, S12 (y del formato de auditoría de S19).

- `/datadesk/activity/`: lista inversa por fecha, agrupada por `commit_id`, con
  actor, tabla, objeto, operación y campos cambiados; paginada. Cada grupo
  muestra el estado `reversible` / `no reversible (merge)` / `ya revertido el …`.
- `POST /datadesk/activity/<commit_id>/revert`: **el commit entero o nada**. Un
  revert parcial de un lote heterogéneo deja la BD en un estado que nadie pidió,
  así que el botón aplica todo el grupo en una transacción (con preview de lo que
  va a hacer).
- Reglas de aplicación, por operación:
  - `create` → borrar el objeto creado (la cascada se lleva sus dependientes, que
    también se revierten por sus propias filas).
  - `update` → escribir el `before` completo del snapshot, no un diff.
  - `delete` → recrear **con el id original** (`Model(id=…, **before)`), porque
    los `CollectionItem` y cualquier referencia externa apuntaban a ese id.
  - `merge` → **rechazado**: el commit entero se marca no reversible.
- Orden dentro del revert: por modelo (lookups → `Issue` → `Stamp`), no por el
  orden en que se registraron. Si no, revertir un alta de serie intenta crear los
  sellos antes que su serie y falla por FK.
- Se rechaza (409 con motivo) si:
  - el commit ya fue revertido (`reverted_at` no nulo);
  - contiene un `merge`;
  - algún objeto cambió después del commit (`updated_at` > `created_at` del
    cambio) — el mensaje dice qué objeto;
  - choca al recrear (PK ocupada, nombre `unique` ya usado, FK destino
    desaparecida).
- El revert se audita como un commit nuevo (`reverts_commit_id` apuntando al
  original) y marca `reverted_at` en las filas originales.

**Lo que el revert no puede devolver**, y la UI lo dice explícitamente al
confirmar: los `CollectionItem` que la cascada borró al eliminar un sello o una
serie **no se recrean** (el snapshot de auditoría es del catálogo, no de las
colecciones de usuario). Se recupera la serie y sus sellos, no quién los tenía.

**Aceptación**: commit de 5 cambios → revert → estado idéntico al previo; revert
de un alta de serie recrea serie y sellos con los mismos ids y colores; segundo
revert del mismo commit → 409 "ya revertido"; objeto modificado después → 409 con
el objeto señalado; commit con `merge` → 409 no reversible; el revert deja sus
propias filas de auditoría con `reverts_commit_id`.

---

### S22 — Cierre

**Depende de**: todas.

- Contrato de teclado completo y consistente (`/`, `j/k`, `N`, `Enter`, `Tab`,
  `Esc`, `Shift+Enter`, `Ctrl+D`, `Ctrl+Z`, `Ctrl+Enter`).
- Barrido de i18n: ningún literal fuera de `{% trans %}`; `datadesk_make_messages --check` en verde.
- Repaso de accesibilidad: foco visible, `label` en inputs, contraste de las
  celdas y del texto atenuado.
- `datadesk/tests/` con servicio, vistas y permisos; objetivo ≥ 80% en
  `datadesk/service.py`.
- `README` del módulo: variables de entorno (`DATADESK_ENABLED`,
  `DATADESK_TLS`), alta de usuario staff, backup previo, cómo apagar el flag, y
  la **receta de allowlist por IP para nginx** (documentada, no implementada).

**Aceptación**: `pytest backend/datadesk` en verde dentro del runner de backend;
`manage.py check --deploy` sin nuevos avisos atribuibles a DataDesk.

---

## 5. Riesgos y cómo se cortan

| Riesgo | Se detecta en | Plan B |
|---|---|---|
| Tabulator no rinde con 2.540 filas | S8/S9 | Grid server-side con HTMX, sin Tabulator; S14–S16 se rehacen con menos JS |
| `CompressedManifestStaticFilesStorage` rompe en prod | S2 | `collectstatic` en el build; probar con `DEBUG=False` antes de S8 |
| Throttling inútil con 4 workers | S3 | `FileBasedCache` compartida (ya previsto) |
| Local sin nginx vs servidor con TLS divergen | S3 | Un solo camino de código; `DATADESK_TLS` solo cambia flags, nunca lógica |
| Cliente y servidor validan distinto | S12/S14 | Una sola fuente: los serializers de DRF validan en servidor, el cliente solo avisa |
| Un `delete` llega por `/apply` y borra de más | S12 | `/apply` rechaza `delete` con 409; borrar solo existe con preview en S17 |
| Merge de colores duplica filas en la M2M | S19 | Inserción explícita en la tabla intermedia con `ignore_conflicts` + borrado del origen, nunca `.set()` ni `.add()` |
| Renombrar un lookup choca con `unique=True` | S19 | 409 `duplicate_name` con `existing_id`; la UI ofrece fusionar |
| Un revert "recupera" una serie pero no quién la tenía | S21 | Los `CollectionItem` borrados por la cascada no vuelven; se avisa en la confirmación |
| `polib` como dependencia nueva | S4 | Commitear `.mo` y borrar el comando |
| Tests en SQLite vs prod en Postgres | S7 | Prohibido lo específico de Postgres en `service.py`; el test lo delata |
| Escritura concurrente desde dos pestañas | S14 | `updated_at` como testigo: aviso, no bloqueo (un solo actor) |
| Aparece una excepción real a nivel de sello | uso diario | Migración aditiva en Postgres; el buffer de S14 diffea campo a campo, así que la UI ya la recoge |

---

## 6. Si solo se hace una cosa

S1 → S2 → S3 → S7 → S8: **login + workbench de lectura**. Es lo único que hace
falta para saber si el enfoque sirve, y no compromete nada del resto.

---

## 7. Estado de implementación

Bitácora de lo construido. Cada paso terminado añade su bloque aquí, con fecha,
ficheros y las decisiones que se tomaron **al implementar** (las que no estaban
en el diseño). Es lo primero que hay que leer al retomar el trabajo.

Rama de trabajo: `development` (sin rama propia todavía). Nada de esto está
commiteado: vive en el working tree. El plan y el diseño están dentro del repo
(`memory-bank/`), no en `~/.opencode`, para que un rebuild del contenedor no los
borre.

### ✅ S1 — Esqueleto de app, flag y montaje (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/__init__.py
backend/datadesk/apps.py                    DataDeskConfig (name="datadesk", verbose_name="DataDesk")
backend/datadesk/urls.py                    app_name="datadesk", "" → DashboardView
backend/datadesk/views/__init__.py
backend/datadesk/views/dashboard.py         DashboardView(TemplateView), provisional
backend/datadesk/templates/datadesk/dashboard.html
backend/datadesk/tests/__init__.py
backend/datadesk/tests/test_mount.py        3 tests
```

Ficheros modificados:

```
backend/_backend/settings.py    DATADESK_ENABLED (env, default False), DATADESK_URL="datadesk/",
                                DATADESK_LOGIN_URL=f"/{DATADESK_URL}login/", "datadesk" en INSTALLED_APPS
backend/_backend/urls.py        montaje condicional al final de urlpatterns
backend/.env.example            DATADESK_ENABLED=False documentado
```

Decisión tomada al implementar (no estaba en el plan): el condicional de
`_backend/urls.py` usa **`django.conf.settings`**, no `from _backend.settings
import ...`. `_backend.settings` es un módulo normal, así que `override_settings`
no lo alcanza y el test no podría encender el flag.

Cómo se prueba: el URLconf se importa una vez por proceso, así que los tests
hacen `clear_url_caches()` + `importlib.reload(_backend.urls)` dentro de un
`override_settings` y lo restauran al terminar la fixture. Reutilizable para S3.

Verificado: `manage.py check` limpio · `spectacular` con **0** referencias a
`datadesk` · **1011** tests de backend en verde (1008 previos + 3 nuevos).

### ✅ S2 — Estáticos vendorizados y plantilla base (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/static/datadesk/vendor/htmx.min.js        htmx 2.0.11
backend/datadesk/static/datadesk/vendor/alpine.min.js      Alpine 3.17.5 (cdn build)
backend/datadesk/static/datadesk/vendor/tabulator.min.js   Tabulator 6.7.1
backend/datadesk/static/datadesk/vendor/tabulator.min.css  Tabulator 6.7.1
backend/datadesk/static/datadesk/vendor/VERSIONS.md        versión, licencia, URL y sha256
backend/datadesk/static/datadesk/datadesk.css              tokens del mockup + primitivas
backend/datadesk/templates/datadesk/base.html              topbar, breadcrumbs, bloques, CSRF
backend/datadesk/tests/conftest.py                         fixture reload_urlconf (movida de test_mount)
backend/datadesk/tests/helpers.py                          UNHASHED_STATIC_STORAGES
backend/datadesk/tests/test_layout.py                      5 tests
backend/datadesk/tests/test_assets.py                      4 tests
```

Ficheros modificados:

```
backend/datadesk/templates/datadesk/dashboard.html   ahora extends base.html
backend/_backend/settings.py                         STATIC_URL "/static/" + STATICFILES_BACKEND según DEBUG
backend/datadesk/tests/test_mount.py                 usa la fixture de conftest + el override de STORAGES
```

Decisiones tomadas al implementar:

- **`STATIC_URL = "/static/"`** (antes `"static/"`, relativa). Con URL relativa los
  assets se rompen en cualquier página de más de un nivel (`/datadesk/issues/12/`);
  whitenoise además los sirve siempre desde la raíz. Único cambio global del paso.
- **`STORAGES` depende de `DEBUG`**: con DEBUG el backend es
  `StaticFilesStorage` (runserver sirve desde los finders, DataDesk funciona sin
  `collectstatic`); fuera de DEBUG sigue `CompressedManifestStaticFilesStorage`.
  El backend con manifest lanza `ValueError` en cualquier asset que no esté en el
  manifest, y CI no ejecuta `collectstatic`: los tests renderizan con el override
  `UNHASHED_STATIC_STORAGES` de `tests/helpers.py`.
- **Se quitaron los `sourceMappingURL`** de los dos ficheros de Tabulator: los
  `.map` no se envían y `collectstatic` avisaba de la referencia rota. Los hashes
  de `VERSIONS.md` son de los ficheros ya limpiados, y un test los compara.
- **Scripts de vendor al final del body, sin `defer`**, justo antes de
  `{% block extra_js %}`: así un script inline de página puede usar Tabulator o
  htmx directamente. Con `defer` el inline correría antes que el vendor.
- **Comentarios de plantilla con `{% comment %}`**: `{# ... #}` multilínea no es
  válido en Django y se imprimía literalmente en el HTML.

Verificado: `collectstatic --noinput` con `DEBUG=False` → 177 copiados, 509
post-procesados, sin avisos · `static('datadesk/datadesk.css')` resuelve a nombre
hasheado con el manifest real · con `DEBUG=True` los 4 assets y `datadesk.css`
responden **200** y `/datadesk/` renderiza la shell con token CSRF · `manage.py
check` limpio · `spectacular` con **0** referencias a `datadesk` · **1020** tests
de backend en verde (1008 previos + 12 de DataDesk).

### ✅ S3 — Login, logout, gate y throttling (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/mixins.py                          DataDeskAccessMixin + wants_json()
backend/datadesk/middleware.py                      DataDeskGateMiddleware
backend/datadesk/views/auth.py                      DataDeskLoginView + throttling + DataDeskLogoutView
backend/datadesk/templates/datadesk/login.html      página standalone (sin topbar ni user slot)
backend/datadesk/templates/datadesk/partials/login_form.html
backend/datadesk/templates/datadesk/forbidden.html  403 para usuario autenticado no-staff
backend/datadesk/tests/test_auth.py                 20 tests
```

Ficheros modificados:

```
backend/datadesk/urls.py                 + login/ y logout/
backend/datadesk/views/dashboard.py      DashboardView hereda DataDeskAccessMixin
backend/_backend/settings.py             CACHES (FileBasedCache), DATADESK_LOGOUT_URL, DATADESK_TLS,
                                         cookies de sesión, SECURE_PROXY_SSL_HEADER condicional,
                                         middleware del gate tras AuthenticationMiddleware
backend/datadesk/templates/datadesk/base.html       formulario POST de "Sign out" en la topbar
backend/datadesk/static/datadesk/datadesk.css       estilos del login (.dd-login*, .dd-field, .dd-alert)
backend/datadesk/tests/test_mount.py     "flag on" ahora espera 302 al login (antes 200)
backend/datadesk/tests/test_layout.py    el test del dashboard entra como staff
backend/.env.example                     DATADESK_TLS=0 documentado
README.md                                cuenta staff, login, DATADESK_TLS y receta nginx de allowlist
```

Decisiones tomadas al implementar:

- **El middleware se salta el gate si `DATADESK_ENABLED` es False** (leído en cada
  request, no al importar) y resuelve los paths exentos con `reverse()`, cayendo a
  "no gatar" si la app no está montada (`NoReverseMatch`). Sin eso, el test de S1
  "flag off → 404" pasaba a 302.
- **Dos respuestas distintas en el gate**: anónimo + navegador → redirect al login
  con `?next=`; anónimo + JSON/HTMX → 401 JSON; autenticado no-staff → 403 (JSON o
  `forbidden.html` según el cliente). El mixin replica el mismo reparto.
- **`wants_json()` mira `HX-Request` y `Accept`**, no la ruta: los endpoints JSON de
  S12 no estarán bajo un prefijo reconocible.
- **Throttle de ventana deslizante**: cada fallo re-arma los 5 minutos
  (`cache.set` con timeout explícito). El 6º fallo y los siguientes dan 429 con
  `Retry-After` (TTL restante de la clave). Un login correcto borra la clave.
- **La IP es `REMOTE_ADDR` a secas**: detrás de nginx es la del proxy, así que la
  clave colapsa al usuario, que es lo que se quiere con un solo actor. `X-Forwarded-For`
  se ignora a propósito.
- **`DATADESK_TLS` se evalúa al importar settings**, así que no se puede probar con
  `override_settings`. El test lo comprueba en un subproceso con el módulo real
  (`python -c` + `DATADESK_TLS=0/1`) y añade un invariante para el proceso actual:
  `SESSION_COOKIE_SECURE is settings.DATADESK_TLS`.
- **`backend/.cache/` ya estaba ignorado** por la regla `.cache` del `.gitignore`
  estándar de Python: no hizo falta tocarlo.
- La página de login **no extiende `base.html`** a propósito: la shell asume un
  usuario y un breadcrumb que en el login no existen. El botón de "Sign in" usa
  `dd-btn-dark` (navy) y no `dd-btn-primary`, y el foco de los inputs es navy: el
  verde queda reservado para commit/apply y para la celda generada. Los enlaces
  genéricos también van en navy.

Verificado: `/datadesk/` anónimo → 302 a `/datadesk/login/?next=/datadesk/` ·
`/datadesk/login/` 200 con el formulario · `/admin/login/` sigue 200 y el health de
la API intacto con el flag encendido · `manage.py check` limpio · `spectacular` con
**0** referencias a `datadesk` · **1040** tests de backend en verde (1020 previos +
20 nuevos).

### ✅ S4 — i18n en/es (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/views/language.py                        set_datadesk_language (POST-only)
backend/datadesk/management/commands/datadesk_make_messages.py   .po → .mo con polib, --check
backend/datadesk/locale/es/LC_MESSAGES/django.po (+ .mo) catálogo español
backend/datadesk/locale/en/LC_MESSAGES/django.po (+ .mo) catálogo inglés (msgstr = msgid)
backend/datadesk/tests/test_i18n.py                      13 tests
```

Ficheros modificados:

```
backend/datadesk/templates/datadesk/base.html          {% translate %} + selector EN/ES como formulario POST
backend/datadesk/templates/datadesk/dashboard.html     textos traducidos
backend/datadesk/templates/datadesk/login.html         título traducido
backend/datadesk/templates/datadesk/partials/login_form.html   textos y mensaje de 429 traducidos
backend/datadesk/templates/datadesk/forbidden.html     textos traducidos
backend/datadesk/urls.py                               language/
backend/datadesk/static/datadesk/datadesk.css         .dd-lang como botones + estado activo
backend/datadesk/tests/conftest.py                     fixture `mounted` compartida (movida de test_auth)
backend/_backend/settings.py                           LocaleMiddleware + DATADESK_LANGUAGES
backend/requirements.base.txt                          polib==1.2.0
backend/Dockerfile.prod                                datadesk_make_messages antes de collectstatic
README.md                                              cómo compilar los catálogos y el --check de CI
```

Decisiones tomadas al implementar:

- **`LANGUAGE_CODE` no se toca** (`en-us`): Django resuelve el catálogo `en` por
  prefijo, así que el inglés sigue funcionando sin cambiar el default del
  proyecto ni el de la API pública.
- **El selector es un formulario POST** (dos `button type=submit name=language`),
  validado contra `DATADESK_LANGUAGES` antes de delegar en `set_language`. Un
  idioma desconocido se ignora y redirige con `next`, que `set_language` valida
  como URL segura. GET → 405.
- **El endpoint de idioma no está exento del gate**: cambiarlo exige sesión
  staff, y el middleware ya lo cubre sin `LoginRequiredMixin`.
- **Los `.mo` se commitean** y además se regeneran en `Dockerfile.prod` antes de
  `collectstatic`, para que la imagen nunca sirva un catálogo viejo. Ojo: el
  `.gitignore` estándar de Python ignora `*.mo`, así que hizo falta una excepción
  (`!backend/datadesk/locale/*/LC_MESSAGES/django.mo`); sin ella la PR pasaba en
  local y fallaba en CI, sin catálogos que cargar.
- **`--check` compara contenido, no fechas**: un checkout de git escribe
  `django.mo` antes que `django.po` (orden alfabético) y el `.mo` parece viejo
  aunque esté al día. Compara `{msgid: msgstr}` de `polib.pofile` contra
  `polib.mofile`, y un test cubre el caso de una traducción editada sin compilar.
- **El test de "assets/locales intactos"** no usa `git status` (fallaría con
  cualquier cambio legítimo en el árbol): comprueba que ningún `.py`/`.html` de
  `datadesk` referencia `assets/locales`, que es el invariante que de verdad
  importa.
- **`Client.logout()` de Django vacía también las cookies del cliente**, así que
  el test de la página de login en español fija `django_language` a mano en vez de
  encadenar login → logout.

Verificado: `curl -b django_language=es /datadesk/login/` devuelve "Acceso a
DataDesk", "Contraseña" y "Entrar"; sin cookie, "Sign in" y "Password" ·
`datadesk_make_messages` compila los 2 catálogos dentro de la imagen ·
`manage.py check` limpio · `spectacular` con **0** referencias a `datadesk` ·
**1053** tests de backend en verde (1040 previos + 13 nuevos).

### ✅ S5 — `updated_at` en Issue y Stamp (2026-11-18)

Ficheros nuevos:

```
backend/issues_api/migrations/0005_issue_updated_at.py   (no se versiona: `migrations/` está en .gitignore)
backend/stamps_api/migrations/0005_stamp_updated_at.py   (ídem)
backend/issues_api/test/test_issue_timestamps.py     4 tests
backend/stamps_api/test/test_stamp_timestamps.py     4 tests
```

Ficheros modificados:

```
backend/issues_api/models.py            Issue.updated_at
backend/stamps_api/models.py            Stamp.updated_at
backend/issues_api/api/serializers/issue_response_serializer.py   exclude = ["updated_at"]
backend/stamps_api/api/serializers/stamp_response_serializer.py   exclude = ["updated_at"]
backend/issues_api/admin.py             IssueAdmin con readonly_fields
backend/stamps_api/admin.py             StampAdmin con readonly_fields
```

Decisiones tomadas al implementar:

- **`null=True` de verdad hace falta**, y está comprobado: con `null=True` y la
  tabla vacía, `migrate` + `loaddata backups/latest__stamps.json` instala 12.763
  objetos y deja los 2.540 issues y 9.558 sellos con `updated_at` NULL. Con el
  campo no nulo eso es un `IntegrityError`.
- **Las migraciones no van al repo**: `.gitignore` ignora `migrations/`, así que
  0005 se genera con `makemigrations` y vive solo en el entorno. En CI no faltan:
  las apps sin migraciones se crean desde los modelos al construir la BD de test.
- **Django rellena las filas existentes al añadir la columna**: si la tabla ya
  tiene datos cuando corre 0005, esas filas quedan con la hora de la migración,
  no NULL (verificado con SQL directo sobre una BD de pruebas). Es el caso de una
  BD de producción que migre; sirve de línea base para S12.
- **`exclude` en vez de `fields` en los serializers de respuesta**: DRF no admite
  `fields` y `exclude` a la vez, así que `fields = "__all__"` pasa a
  `exclude = ["updated_at"]`. El schema de DRF queda con **0** menciones al campo,
  o sea que `/api/v1/` no cambia.
- **`ModelAdmin` explícito** en las dos apps: `admin.site.register(Model)` no
  permitía `readonly_fields`.
- **Los fixtures de test son de ámbito de módulo**, no globales: un test que usa
  `stamps_table` tiene que importar también `issues_table`, `colors_table`,
  `years_table`, `countries_table`, `stamp_types_table` y `print_types_table`, o
  pytest no resuelve la cadena de dependencias.

Verificado: `migrate` aplica 0005 en las dos apps y `migrate <app> 0004` las
revierte sin error · `loaddata` del backup de julio deja los timestamps en NULL ·
un `save()` posterior mueve el campo · `manage.py check` limpio · `spectacular`
sin rastro del campo · **1062** tests de backend en verde (1053 previos + 8
nuevos + el test de `--check` de S4). Las BD de pruebas (`s5_scratch`,
`s5_probe`) se borraron; `backend_db` sigue intacta y vacía.

### ✅ S6 — `DataDeskChange` y escritor de auditoría (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/models.py            DataDeskChange (commit_id, user, model_label, object_id,
                                     operation, before, after, reverted_at, reverts_commit_id)
backend/datadesk/audit.py             snapshot(), record(), new_commit_id(), model_label()
backend/datadesk/admin.py             DataDeskChangeAdmin de solo lectura
backend/datadesk/tests/test_audit.py  14 tests
```

Generado (no versionado, `migrations/` está en `.gitignore`):
`datadesk/migrations/0001_initial.py`.

Decisiones tomadas al implementar:

- **Las claves del snapshot son `attname`** (`issue_id`, `year_id`, no `issue`):
  así `Stamp(**snapshot)` reconstruye la fila tal cual, que es el contrato que
  necesita S21. Con el nombre del campo, Django exige una instancia, no un id.
- **`id` se excluye por `primary_key`**: en Django 6 el `AutoField` no llega con
  `editable=False`, así que filtrar solo por `editable` lo dejaba dentro.
- **`updated_at` no entra** (lista negra explícita) aunque `auto_now` ya lo marca
  como no editable: si algún día deja de serlo, el snapshot no cambia.
- **`Decimal` se guarda como string y `date` como ISO-8601**, y un test comprueba
  que el dict sobrevive a `json.dumps`/`json.loads` sin cambios. Ojo: ese string
  solo aparece si la instancia viene de la BD (un `DecimalField` recién creado en
  memoria sigue siendo `float`); DataDesk siempre lee de la BD.
- **`record()` valida la operación** contra `DataDeskChange.OPERATIONS` y guarda
  `user=None` para actores anónimos, para que un `AnonymousUser` no reviente la FK.
- **El admin es de solo lectura en los tres permisos** (`add`, `change`,
  `delete`): el trail no se toca a mano ni se borra.

Verificado: `manage.py check` limpio · **1076** tests de backend en verde (1062
previos + 14 nuevos), ejecutados en la imagen de test (CI). `backend_db` sigue sin
tocar; las migraciones 0005 de S5 y 0001 de DataDesk se aplicarán cuando se lance
`migrate`.

### ✅ S7 — Registry de lookups y querysets de lectura (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/registry.py              8 lookups con modelo, label traducible, columna, numeric y refs
backend/datadesk/service.py               issue_queryset(), stamp_queryset(), missing_data_report()
backend/datadesk/tests/test_service_read.py  12 tests
```

Ficheros modificados:

```
backend/datadesk/locale/es/LC_MESSAGES/django.po (+ .mo)   etiquetas de los 8 lookups traducidas
backend/datadesk/locale/en/LC_MESSAGES/django.po (+ .mo)   mismas entradas en inglés
```

Decisiones tomadas al implementar:

- **`Lookup` es un dataclass congelado**, no un dict suelto: el modelo, la
  columna que identifica la fila (`year` para años, `name` para el resto), si es
  numérico y las relaciones entrantes quedan tipados y verificables.
- **Las `refs` son `(model_label, field_name)`** y hay un test que resuelve cada
  una con `apps.get_model()` y comprueba que el campo existe: si mañana se
  renombra una FK, el test lo caza antes que el merge de S19.
- **Orden del workbench: `year__year`, `date` (`nulls_last` explícito), `name`**,
  ascendente. Es el valor por defecto, no una regla: S8 permitirá ordenar por
  cualquier columna. Los NULL se fuerzan al final para no depender del motor.
- **`face_value` se cuenta con `= ""`, no con `isnull`**: la columna no admite
  NULL, así que "sin facial" solo puede ser cadena vacía. `image` sí comprueba
  NULL **y** `""`.
- **`stamp_queryset()` ordena por `id`**: el orden definitivo del grid del
  workspace (edifil, etc.) es decisión de S10; aquí solo se garantiza estabilidad.

Verificado: `issue_queryset()` consume **1** query con los 7 `select_related` y el
`Count` (`assertNumQueries`) · `stamp_queryset()` consume 2 (sellos + colores) ·
los 6 contadores cuadran sobre un dataset con huecos explícitos · `manage.py
check` limpio · **1088** tests de backend en verde en la imagen de test (1062
previos + 12 nuevos + 14 de S6).

### ✅ S8 — Workbench de solo lectura (2026-11-18) ← primer hito

Ficheros nuevos:

```
backend/datadesk/views/workbench.py       WorkbenchView + COLUMNS + grid_config()
backend/datadesk/views/workbench_api.py   IssueGridJsonView (JSON, no DRF)
backend/datadesk/templates/datadesk/workbench.html   filtros + toolbar + #workbench
backend/datadesk/static/datadesk/workbench.js        Tabulator, URL, localStorage, badge
backend/datadesk/tests/test_workbench_api.py         27 tests
```

Ficheros modificados:

```
backend/datadesk/service.py          IssueFilters, IssuePage, ATTENTION_KEYS, SORT_FIELDS,
                                     filter_issues(), sort_issues(), issue_page(), serialize_issue()
backend/datadesk/urls.py             issues/ y grid/issues
backend/datadesk/templates/datadesk/dashboard.html   enlace al workbench
backend/datadesk/static/datadesk/datadesk.css       filtros, toolbar, columnas y densidad de Tabulator
backend/datadesk/locale/{es,en}/…/django.po (+ .mo)  25 msgids nuevos
```

Decisiones tomadas al implementar:

- **Los tres filtros de "needs attention" a nivel de sello usan `Exists`**, no
  joins: un join multiplicaría filas y rompería el `Count("stamps")` del grid.
  Los de serie (sin país, sin fecha) y `no_stamps` también, así los seis comparten
  forma y el badge y el filtro no pueden divergir.
- **El badge marca solo los tres huecos acordados** (`no_country`, `no_date`,
  `no_stamps`) y se calcula de la fila ya serializada: cero queries extra. Los
  huecos de sellos siguen siendo contadores del dashboard (S20).
- **`SORT_FIELDS` es una lista blanca** en el servicio: un `sort[0][field]`
  desconocido o malicioso cae al orden cronológico por defecto, no a un error.
- **La agrupación por año es por página**, no sobre el dataset: el precio de
  agrupar globalmente sería renunciar a la paginación server-side. Queda como
  limitación consciente hasta que S9 diga si el volumen permite otra cosa.
- **La fila expandible con sus sellos se pospone a S10**: el enlace al workspace
  aún no existe.
- **Los títulos de columna los renderiza Django** dentro de un `json_script`, así
  `workbench.js` no contiene texto de interfaz y las traducciones siguen saliendo
  del catálogo.
- **Filtros en la URL, columnas en `localStorage`**; el buscador lleva 300 ms de
  debounce y `page`/`size` se limpian al cambiar un filtro.
- **`page` se recorta a `last_page`** y `size` se limita a 200: un `size=100000`
  no puede tumbar el endpoint.

Verificado con los **datos reales** (2.540 series, 9.555 sellos): primera página
de 100 filas en **138 ms** (26 páginas), `attention=no_stamps` en 63 ms, endpoint
con las 18 claves por fila, página y grid a 302 sin sesión y a 200 con usuario
staff · `manage.py check` limpio · `spectacular` con **0** referencias a
`datadesk` · **1115** tests de backend en verde en la imagen de test (1088 previos
+ 27 nuevos).

### ✅ S9 — Rendimiento e índices (2026-11-18)

Sin cambios de código: el entregable es `memory-bank/datadesk-perf.md` con los
números, los planes y la decisión, más un test que fija el contador de queries.

Decisiones tomadas al medir:

- **No se añade ningún índice.** El cuello de botella no es leer: en la primera
  página `Planning Time` son **42 ms** y `Execution Time` **24 ms**. El coste es
  planificar el join de ocho tablas con filas de 2.350 bytes, no recorrer 2.540
  filas. La misma SQL por cursor tarda 59,9 ms y por el ORM 62,3 ms: el ORM y la
  serialización de 100 filas son ~2 ms.
- **`Issue.name` no puede aprovechar un btree**: `name__icontains` se compila a
  `UPPER(name::text) LIKE UPPER('%real%')`, con comodín inicial. Haría falta
  `pg_trgm` + GIN, y hoy la búsqueda tarda **2 ms de ejecución**.
- **El filtro por año ya usa el índice de la FK** (`year_id`), y el orden por
  defecto ordena por `year.year` a través del join, así que un compuesto
  `(year_id, date)` no entra en el plan.
- **Las tres colas de sello son semi joins sobre 9.558 filas**: 32–49 ms de
  ejecución con `Seq Scan`; un índice parcial (`face_value = ''`) no gana a este
  volumen. `Issue.country` y `Issue.stamp_type` ya son FKs indexadas.
- **La última página no se degrada** (p95 71,5 ms vs 70,3 ms): el `top-N
  heapsort` ya recorre el conjunto y el `OFFSET` no añade un escaneo.
- **El contador de queries es constante** (2: `COUNT` + página) con `size` 10,
  50, 100 y 200, y los sellos de una serie son 2 queries. Se añade un test que
  lo fija (`TestPageCost`).
- **La serie más larga real tiene 57 sellos**, no 24: corregida la aceptación de
  S10 y la nota de contexto.

Peor p95 medido: **84 ms** (`stamps_without_colors`), muy por debajo de los
300 ms de aceptación. Volumen real: 2.540 series / 9.558 sellos.

### ✅ S10 — Workspace `mode=edit` de solo lectura (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/views/workspace.py                  IssueWorkspaceView + metadata + config
backend/datadesk/templates/datadesk/issue_workspace.html   franja y #stamp-grid
backend/datadesk/static/datadesk/issue_workspace.js        Tabulator de solo lectura + Esc
backend/datadesk/tests/test_workspace.py                   21 tests
```

Ficheros modificados:

```
backend/datadesk/service.py                  stamp_rows(), serialize_stamp()
backend/datadesk/views/workbench.py          grid_config(): openText + issueUrlPrefix
backend/datadesk/static/datadesk/workbench.js       columna ↗, filas seleccionables, Enter
backend/datadesk/urls.py                     issues/<int:pk>/
backend/datadesk/templates/datadesk/base.html       <html lang> con get_current_language
backend/datadesk/static/datadesk/datadesk.css       franja, chips, celda de imagen
backend/datadesk/locale/{es,en}/…/django.po (+ .mo) 15 msgids nuevos
```

Decisiones tomadas al implementar:

- **Sin herencia de valores** (ver §2): cada celdilla muestra lo que guarda el
  sello y la franja lo que guarda la serie. Hubo un mapa `inherited` que se
  calculaba en el servicio y se retiró al comprobar que los valores de la serie
  son del conjunto, no de cada sello (832 sellos con el mismo MNH que su serie
  son coincidencia, no copia).
- **Las filas viajan dentro de la página** (`json_script`), sin endpoint nuevo:
  una serie son decenas de filas (57 como techo real) y un segundo viaje cuesta
  más que el payload.
- **Formateo en la vista** con `date_format` + `number_format`, que sí leen el
  locale activo: `SHORT_DATE_FORMAT` da 12/05/1987 en es y 05/12/1987 en en, y
  los miles siguen CLDR (espacio duro en es, coma en en — no el punto del
  mockup, que era una convención de diseño).
- **`base.html` no tenía idioma real en `<html lang>`**: `LANGUAGE_CODE` no está
  en el contexto (no hay context processor de i18n) y siempre salía `en`; ahora
  sale de `{% get_current_language %}`.
- **Enlace ↗ por fila, no navegación al clic**: `selectableRows: 1` para que
  `Enter` abra la fila enfocada, pero un clic solo selecciona — abrir una serie
  por accidente mientras se lee la tabla era peor que un clic de más.
- **`Esc` usa `history.back()`** cuando se llega desde el workbench, así los
  filtros siguen puestos sin serializarlos en la URL del workspace; si no hay
  referrer, va a `issuesUrl`.
- **El grid no pagina** (`height: false`): 57 sellos son una tirada de scroll, y
  paginar una serie rompería la lectura de la herencia de un vistazo.

Verificado con los datos reales: la serie de 57 sellos pinta **28 KB en 14 ms y
3 queries** (serie + sellos + colores); una serie corta, 11 ms. Serie
inexistente → 404, anónimo → 302 al login, no staff → 403 · `manage.py check`
limpio · `spectacular` con **0** referencias a `datadesk` · **1137** tests de
backend en verde (1116 previos + 21 nuevos).

### ✅ S10b — Pulido del workspace: miniaturas, colores, icono y herencia (2026-11-18)

Ficheros nuevos:

```
backend/datadesk/images.py                     índice <año>/<código>.webp + resolución segura
backend/datadesk/palette.py                    tono estable por nombre de color
backend/datadesk/views/images.py               StampImageView (staff, FileResponse, ETag)
backend/datadesk/tests/test_images.py          30 tests (imágenes, borde y paleta)
```

Ficheros modificados:

```
backend/_backend/settings.py            DATADESK_STAMP_IMAGES
backend/docker-compose.dev.yml          bind ../frontend/assets/stamps -> /srv/stamp-images (ro)
backend/.env.example                    variable documentada
backend/datadesk/service.py             has_image, colores con tono, cola "sin imagen" por archivo
backend/datadesk/views/workspace.py     image_url por fila, columna has_image
backend/datadesk/static/datadesk/issue_workspace.js   chips con tono, miniatura
backend/datadesk/static/datadesk/workbench.js        chevron SVG + doble clic
backend/datadesk/static/datadesk/datadesk.css        tonos de chip, thumb, chevron
backend/datadesk/templates/datadesk/issue_workspace.html  aviso de que la serie describe el conjunto
README.md                               cómo se montan las imágenes y qué pasa si faltan
```

Decisiones tomadas al implementar:

- **Las imágenes se leen del montaje, no de la BD**: `Stamp.image` está vacío en las
  9.558 filas y los archivos viven con el frontend. En datos reales hay 6.625 webp y
  **8.419 de 9.558 sellos (88%) encuentran el suyo**; los 1.139 restantes pintan el
  cuadradito. Importar a `MEDIA_ROOT` queda como tema aparte (también serviría a la app
  Flet), porque exige `MEDIA_URL`/`MEDIA_ROOT`, servir `/media/` en producción y cambia
  lo que devuelve la API.
- **La carpeta va montada de solo lectura**, así que añadir una imagen en la VM no
  obliga a reconstruir nada. En dev el bind está en `docker-compose.dev.yml`
  (`../frontend/assets/stamps` → `/srv/stamp-images`). **En producción no se toca
  `backend/docker-compose.prod.yml`** (2026-11-19): el despliegue usa un único compose
  con los tres contenedores (db, backend y frontend) y solo él sabe dónde viven las
  imágenes; ahí se define el montaje y se deja `DATADESK_STAMP_IMAGES` apuntando a esa
  ruta, que puede cambiar de sitio sin tocar código. Una ruta que no existe —o que aún
  no existe— tampoco es un error: se pinta `no_stamp.webp`.
- **Un índice cacheado 60 s, pasado a quien resuelve en lote**: la caché compartida es de
  fichero y leerla cuesta ~1 ms por llamada. La primera versión llamaba a `image_path()`
  por sello (9.558 veces) y la cola tardaba **11,5 s**; con el índice pasado y
  comprobación de pertenencia baja a **36 ms**, y el workspace vuelve a 15 ms.
- **La cola "sin imagen" cuenta archivos que faltan**, no `Stamp.image`: es lo que la
  pantalla puede enseñar. Hoy reporta 1.139.
- **Los tonos de color se derivan del nombre** (`palette.py`): mapa de raíces en español
  (el catálogo lo es) con prioridad para los marrones sobre los rojos ("Castaño rojizo"
  es marrón), `Multicolor`/`Cuatricomía` al tono neutro y `md5 % 8` como reserva estable
  (el `hash()` de Python está salteado por proceso y cambiaría el color entre workers).
- **El icono de abrir es un chevron SVG en línea** en vez de `↗`, que prometía abrir otra
  pestaña, y la fila se abre también con **doble clic**; un clic simple sigue solo
  seleccionando.
- **La herencia desapareció** (2026-11-18). El primer intento fue mejorar su
  legibilidad —fondo teñido, barra interior y una leyenda bajo la franja—, pero al
  revisar el significado quedó claro que el concepto no se sostiene: la tirada y
  los valores de mercado de la serie describen el conjunto (que vale menos que la
  suma de sus sellos), el nombre es de cada sello y la descripción nunca coincide
  (0 de 9.558). Se retiraron el mapa `inherited`, el tinte, la leyenda, el `⟲` de
  la franja y los tests; la franja queda con un aviso corto de que la serie
  describe el conjunto. En S14 el buffer compara campo a campo contra la fila
  original, sin estados "heredado"/"propio".
- **El hueco de imagen usa `no_stamp.webp`**, copiado a
  `datadesk/static/datadesk/` porque el montaje solo cubre `stamps/` y el
  placeholder vive en `frontend/assets/`. Se sirve como estático de la app.
- **La imagen se sirve por `/datadesk/stamps/<id>/image`**, detrás del gate de staff, con
  `Content-Type: image/webp`, `Cache-Control: private, max-age=604800` y ETag por
  mtime+tamaño, así que una revisita es un 304. No se publica por `/media/` ni por
  `STATICFILES_DIRS`, que arrastraría 206 MB a `collectstatic`.

Verificado con los datos reales dentro del contenedor: el índice se construye en 1 ms,
la serie de 57 sellos pinta **15,5 ms con las 57 miniaturas**, la cola tarda 36 ms y
reporta 1.139 sin imagen; anónimo → 302 en página e imagen · `manage.py check` limpio ·
`spectacular` con **0** referencias a `datadesk` · **1167** tests de backend en verde.

### ✅ S11 — `mode=new` en seco (2026-11-19)

Ficheros nuevos:

```
backend/datadesk/tests/test_workspace_new.py  23 tests (nuevo, prefijado, filas, modos, acceso)
```

Ficheros modificados:

```
backend/datadesk/urls.py                                issues/new/ antes del int:pk
backend/datadesk/views/workspace.py                     IssueCreateView, last_issue_prefill,
                                                        series_form_fields, NewRowSettings
backend/datadesk/templates/datadesk/issue_workspace.html formulario de serie + control rows=N
backend/datadesk/templates/datadesk/workbench.html      enlace «+ New series» en la barra
backend/datadesk/static/datadesk/issue_workspace.js     filas new-<n>, touched, beforeunload, prefill
backend/datadesk/static/datadesk/datadesk.css           .dd-input, .dd-rows, .dd-req, .dd-hint-flash
backend/datadesk/locale/{en,es}/…/django.po (+ .mo)     7 msgids nuevos
```

Decisiones tomadas al implementar (D1–D5 de la revisión):

- **El prefijado es `country` + `year`, y nada más** (D1). Se descartó el
  "país/año automáticos + chip de clasificatorios" por superficie sin datos que
  lo justifiquen; si S16 demuestra que se teclean los mismos seis campos serie
  tras serie, se añade entonces. Sin series en la BD, `prefill` es `None` y el
  botón no se pinta (un botón deshabilitado invita a pulsarlo).
- **`rows=N` nace en 4, rango 1–100, y S16 no lo cambia** (D2). Derivarlo de la
  última serie generaría 57 filas vacías tras una serie larga. Cambiar `N`
  crece por el final y encoge **solo** mientras la última fila esté intacta; por
  debajo de una fila tocada no baja. El borrado de filas sueltas llega con la
  edición (S13), no aquí.
- **El nombre de la serie es un valor por defecto, no una herencia** (D3): las
  filas nacen `touched: false` y siguen al campo `name`; el primer
  `cellEdited` las marca y dejan de seguir. Ese flag es la línea base de S14.
  En este paso no hay editores, así que el hook existe pero solo lo ejercita el
  nombre; se dejó puesto para no reinventarlo en S13.
- **Ids `new-1`, `new-2`…** (D4), con el prefijo enviado por el servidor en la
  configuración: los ids reales son números y no hay colisión posible, y el
  script no guarda convenciones propias. Nunca se reutiliza un número.
- **`beforeunload` solo con la pantalla sucia** (D5): se compara una instantánea
  de los campos del formulario y de los ids de las filas con la del arranque.
  Volver a lo prefijado deja de estar sucio, que es lo correcto: no hay nada que
  perder. El aviso de `Shift+Enter` es texto fijo bajo el grid que parpadea al
  pulsar el atajo, no un tooltip, porque un atajo inerte no recibe hover.
- **El formulario es un `div`, no un `<form>`**: sin endpoint no hay nada que
  enviar, y un `<form>` recargaría la página al pulsar Intro en un campo,
  tirando el borrador que este paso promete descartar solo al salir.
- **El prefijado viaja en la página** (dentro de `stamp-config`) y el botón lo
  reaplica en cliente: así no se pierde lo ya montado en el grid y no hace falta
  un endpoint nuevo para leer "la última serie".
- **Ruta con `int:` en el detalle** y `issues/new/` declarada antes: `new` no
  compite con el patrón de id, y un id no numérico da 404 en vez de abrir un
  workspace vacío.
- **El workbench gana un enlace «+ New series»**: sin él la pantalla solo se abre
  escribiendo la URL, y su aceptación pide comprobarla a mano. El flujo completo
  (bucle «Create another», atajos) sigue siendo S16.

- **El año se teclea, no se elige** (2026-11-19, tras revisión con el usuario):
  con `select` no había forma de crear una serie del año en curso, porque la fila
  de `Year` no existe hasta que alguien la crea. Ahora es `input[type=number]` con
  los años existentes como `<datalist>`, el prefill lleva el **número** (no el id)
  y el servidor resolverá `get_or_create` al guardar. Rango 1800–año actual+2 y
  aviso «se creará al guardar» cuando el número no está en la lista; sin el
  rango, `126` pasaría y crearía una fila basura que luego hay que fusionar.
  Efecto colateral anotado, no corregido: `↺ Use last issue` es un no-op mientras
  país y año conserven el valor prefijado — solo se nota tras cambiarlos.

Verificado: `pytest datadesk/tests` → **178 en verde** (150 previos + 28 nuevos);
suite completa **1189 en verde** · prefijado con la última fila real (el año de
la otra serie es posterior: se ordena por `-id`, no por año) · base de datos vacía
→ sin prefill ni botón · anónimo → 302 al login, no staff → 403 · `manage.py
check` limpio · `spectacular` con **0** referencias a `datadesk`.

### ⏭ Siguiente: S12

Núcleo de escritura, sin interfaz: `POST /datadesk/issues/create` (serie + sellos
anidados, todo o nada) y `POST /datadesk/apply` (filas existentes, savepoint por
fila), con auditoría y validación por serializers de DRF.




### ✅ S12 — Núcleo de escritura (2026-11-19)

Ficheros nuevos:

```
backend/datadesk/rules.py                 MIN_SERIES_YEAR, YEARS_AHEAD, series_year_bounds()
backend/datadesk/write.py                 create_series(), apply_changes(), create_lookup(),
                                          WriteError, RowRejected, ApplyResult, CreatedSeries, LookupResult
backend/datadesk/views/write_api.py       JsonPostView + IssueCreateJsonView, ApplyJsonView, LookupCreateJsonView
backend/datadesk/tests/test_write.py      38 tests (transacciones, auditoría, conflictos, lookups)
backend/datadesk/tests/test_write_api.py  18 tests (gate, CSRF, códigos de estado, envelope)
```

Ficheros modificados:

```
backend/datadesk/urls.py                  issues/create, apply, lookups/<key>/create (sin barra final)
backend/datadesk/views/workspace.py       IssueCreateView → IssueNewView; las reglas del año se van a rules.py
```

Decisiones tomadas al implementar (no estaban en el plan):

- **`rules.py`**: el rango del año estaba en `views/workspace.py`, pero el
  escritor también lo necesita y una vista no debe importarse desde la capa de
  escritura. Las dos leen la misma función, así que el formulario no puede
  aceptar un año que el servidor rechace.
- **`IssueCreateView` → `IssueNewView`**: `IssueCreateJsonView` es el endpoint y
  tener dos "Create" a un import de distancia era una trampa. La ruta no cambia.
- **El año implícito no se audita**: `get_or_create` de `Year` ocurre dentro de
  la transacción, así que solo sobrevive si la serie se crea, y revertir la serie
  deja una fila `Year` vacía que es inofensiva y reutilizable. Auditarla habría
  roto el recuento de S12 (una serie de 8 sellos = 9 filas, no 10) y S21 no
  tendría que decidir entre borrar un año referenciado o no.
- **Los colores no pasan por el serializer**: DRF rechaza `colors: []` («this
  list may not be empty») porque el M2M no lleva `blank=True`, pero un sello sin
  colores es un hueco que las colas de «needs attention» cuentan, no un error que
  el usuario no pueda arreglar desde el grid. El campo se quita del serializer
  (`_serializer()`), los ids se resuelven a filas y se aplican con un `set()`
  dentro de la transacción, como pedía el plan.
- **`""` en columna nullable → `None`**: el formulario manda cadena vacía al
  limpiar una fecha y el `DateField` la rechazaría. Se normaliza en
  `_prepare_patch()`, no en cada serializer.
- **`/apply` responde 200 aunque rechace filas**: los rechazos son de fila, no de
  petición, y un 400 obligaría al cliente a mirar el cuerpo igualmente. 400
  queda para el sobre (no es lista, modelo u operación desconocidos, más de 500)
  y 409 para `delete`. `success` es `false` si algo se rechazó, `applied` y
  `rejected` dicen el resto.
- **Bloqueo de fila en las actualizaciones**: `select_for_update()` antes de
  comparar `expected_updated_at`, para que la comprobación no pueda perder una
  carrera con otra pestaña. `updated_at` nulo (backups de julio) no es conflicto.
- **Mensajes en inglés sin traducir**: los errores de DRF que devuelve el mismo
  endpoint (``This field is required.``) tampoco están en el catálogo, así que
  traducir solo los propios daría una respuesta a medias. La traducción se hará
  en la pantalla (S16), que decide qué texto enseñar por código de error.
- **`datadesk/tests/test_write_api.py` separado**: el plan pedía un solo
  `test_service_write.py`, pero CSRF, gate y códigos de estado no son propiedad
  del escritor. Los dos ficheros suman 56 tests.
- **No se reformateó código ajeno**: `black` no está aplicado al repo (87
  ficheros cambiarían), así que solo se formatearon los ficheros nuevos; el
  reformateo cosmético que `black` hizo en `workspace.py` se revirtió para que el
  diff de S11+S12 no arrastre líneas que nadie tocó.

Verificado: `pytest datadesk` → **234 en verde** (178 previos + 56 nuevos); suite
completa **1250 en verde** · `manage.py check` limpio · `spectacular` con **0**
referencias a `datadesk` · `datadesk_make_messages --check` sin cambios (S12 no
añade cadenas al catálogo).

### ✅ S13 — Commit de una fila desde el grid (2026-11-19, segundo hito)

Ficheros nuevos:

```
backend/datadesk/tests/test_workspace_edit.py  14 tests (baseline, columnas, strip, ida y vuelta)
```

Ficheros modificados:

```
backend/datadesk/service.py                 serialize_stamp() añade updated_at (dato de fila, no columna)
backend/datadesk/write.py                   ApplyResult.rows → data.rows [{index, id, updated_at}]
backend/datadesk/views/workspace.py         STAMP_COLUMNS con patch/editor; series_values();
                                            workspace_config(series=…) con applyUrl, series y texts;
                                            fuera issue_metadata(), _display() y _name_of()
backend/datadesk/templates/datadesk/issue_workspace.html  un solo formulario para los dos modos,
                                            barra de commit del modo edit
backend/datadesk/templates/datadesk/base.html              <meta name="csrf-token">
backend/datadesk/static/datadesk/issue_workspace.js        editMode(): editores, Shift+Enter, Save,
                                            estados de fila y mensajes del servidor
backend/datadesk/static/datadesk/datadesk.css              dd-row-dirty/saved/error, dd-status-*
backend/datadesk/locale/{en,es}/LC_MESSAGES/django.po     5 textos de la barra + 2 de la plantilla
backend/datadesk/tests/test_workspace.py                   el test de herencia mira `form_fields`
```

Decisiones tomadas al implementar:

- **La franja de la serie pasa a ser un formulario** y comparte las definiciones
  de S11 (`SERIES_FIELDS` + `series_form_fields`), así que escribir una serie y
  corregirla usan los mismos quince campos y las mismas listas de opciones. Por
  eso desaparecen `issue_metadata()`, `_display()`, `_name_of()` y los tests de
  formato por idioma: **la franja ya no formatea números ni fechas con la
  locale**, los muestra como los manda el campo (`1.20`, `1987-05-12`), que es lo
  que un `input` necesita. Si se echa de menos la lectura formateada, el sitio es
  S22 (vista de sólo lectura), no un formato a medias aquí.
- **`updated_at` viaja como dato de fila, no como columna**: el grid lo necesita
  para el `expected_updated_at`, pero nadie lo lee. `serialize_stamp()` lo añade
  y `STAMP_COLUMNS` no lo declara, así que no hay celda que lo muestre.
- **`/apply` devuelve la referencia de cada fila escrita** (`data.rows` con
  `index`, `id` y `updated_at`). Sin eso el cliente no tiene la nueva línea base
  y la segunda edición de la misma fila se rechazaría como pisada. Es un cambio
  mínimo del contrato de S12, no un endpoint nuevo.
- **`patch` en la definición de columna**: la presencia de `patch` (el campo del
  modelo) es lo que decide si la celda tiene editor; `colors` y `has_image` no lo
  llevan y quedan de sólo lectura. El script no conoce ningún nombre de campo.
- **El editor abierto se cierra antes de leer**: `Shift+Enter` hace `blur()`
  primero, porque Tabulator escribe el valor tecleado en la fila al perder el
  foco y comitear antes mandaría el valor viejo. La alternativa (cancelar el
  evento y leer el DOM del editor) es código que Tabulator ya tiene resuelto.
- **Al rechazar, la celda se revierte y la franja no**: un valor suelto se
  vuelve a teclear en dos segundos, pero borrar medio formulario que el usuario
  acaba de rellenar es peor que el error. La fila se queda marcada en rojo con el
  mensaje del servidor y la franja conserva lo tecleado.
- **`Esc` deja de navegar si el foco está en un campo**: con la franja editable,
  el primer `Esc` pertenece al control (hace `blur`), no a "volver al workbench".
- **Mensajes de la barra desde el servidor** (`config.texts`), como los títulos de
  columna: el JS sigue sin texto de interfaz. Los textos de los errores son los
  que devuelve `/apply` (DRF incluido), en inglés hasta S16.
- **`<meta name="csrf-token">` en `base.html`**: `fetch` no pasa por HTMX ni por
  un `<form>`, y leer la cookie obligaría a depender de que no sea `HttpOnly`.
- **Barra de estado y botón Save**: el atajo es el camino corto, pero una acción
  que sólo existe en un atajo no se descubre. El botón llama a la misma función.
- **El objetivo del commit se decide por el foco *y* por lo que está sucio**
  (corregido el 2026-11-19 al primer uso real): pulsar el botón mueve el foco
  fuera del campo —el botón no está dentro de `#series-form`—, así que mirar solo
  el foco hacía que Save respondiera «no ha cambiado nada» con la franja llena de
  cambios. Ahora: foco en la franja y sucia → serie; si no, la fila pendiente; si
  no hay fila, la serie sucia. Y la franja avisa al teclear («Edited, not saved
  yet.»), que era la otra mitad del problema: no había señal de que hubiera algo
  por guardar.

Verificado: `pytest datadesk` → **246 en verde** (234 previos + 14 nuevos − 2 de
formato que ya no aplican); suite completa **1262 en verde** · `manage.py check`
limpio · `pnpm`-free: `node --check` del JS · catálogos recompilados y
`datadesk_make_messages --check` en verde · HTML comprobado a mano: los quince
campos llegan con su valor, el `select` de país marcado, la barra de commit y el
meta del token presentes.

### ✅ S14 — Change set en cliente (2026-11-19)

Ficheros modificados:

```
backend/datadesk/views/workspace.py             texts (saving), plurals con ngettext, storageKey,
                                                schemaVersion, undoLimit; BUFFER_SCHEMA, UNDO_LIMIT
backend/datadesk/templates/datadesk/issue_workspace.html  contador, Undo/Redo/Discard/Save changes,
                                                barra de recuperación, aviso de otra pestaña
backend/datadesk/static/datadesk/issue_workspace.js       buffer por objeto, undo/redo, localStorage,
                                                recuperación, storage event, Ctrl+Z de mode=new
backend/datadesk/static/datadesk/datadesk.css             dd-recover, dd-tabnotice, dd-count, :disabled
backend/datadesk/locale/{en,es}/LC_MESSAGES/django.po     8 textos + 2 entradas plurales
backend/datadesk/tests/test_workspace_edit.py             5 tests nuevos (plurals, ajustes, pie)
backend/datadesk/tests/test_workspace_new.py             1 test (new no lleva change set)
backend/datadesk/tests/test_i18n.py                      el test de catálogo entiende msgstr_plural
```

Decisiones tomadas al implementar:

- **JS a mano, no Alpine** (se aparta de lo que decía el diseño): el pie son
  cuatro nodos y un contador, y Alpine habría metido un segundo idioma en un
  fichero que ya es JS plano, con su paso de compilación en cliente. El estado
  sigue siendo un `Map` por objeto, que es lo que el diseño pedía; lo que cambia
  es quién pinta.
- **Guardar sigue existiendo en este paso** (`Save changes`, `Shift+Enter`):
  S15 añade el panel de revisión y la confirmación, pero un paso que deja la app
  sin forma de guardar no es entregable. El commit por lotes ya está hecho
  (`/apply` acepta N cambios desde S12); S15 le pone delante el diff y la
  decisión. Con esto, el commit de una fila de S13 queda sustituido: ahora
  `Shift+Enter` guarda el buffer entero.
- **El contador cuenta campos, no objetos**: es lo que el panel de S15 va a
  listar (`stamp:412 → edifil_code`), así que el número del pie y el del panel
  no pueden discrepar.
- **Plurales en servidor con `ngettext`**, y el navegador solo sustituye
  `%(count)s`. Los catálogos ganan dos entradas plurales y el test de i18n
  aprende a leer `msgstr_plural` (antes habría dado por vacías todas las
  traducciones plurales).
- **El borrador nunca se restaura solo** y, mientras la oferta está en pantalla,
  `persist()` **no lo borra**: sin ese detalle, el guardado diferido de 400 ms
  habría echado a la basura el draft del día anterior justo al abrir la página.
- **Granularidad del undo en la franja**: `input` recalcula el diff (contador en
  vivo) y `change` apunta el paso de deshacer. Un paso por tecla convertiría
  `Ctrl+Z` en deletrear lo que acabas de escribir.
- **`Ctrl+Z` es nuestro salvo dentro de los campos de la franja**, donde se deja
  el undo del navegador; en el grid manda el nuestro, que es donde el usuario
  espera deshacer una edición.
- **Descartar revierte los valores, borra el borrador y vacía la pila**: dejar
  historial después de descartar permitiría "rehacer" un draft que ya no existe.
- **En `mode=new` no se persiste nada y el undo vive en memoria**, como pedía el
  diseño: un borrador de serie nueva se termina ahora o se empieza otra vez.
- **Verificado con un arnés desechable** (`jsdom` + un Tabulator falso, fuera del
  repo: no hay Node en el proyecto): 33 comprobaciones sobre contador, volver al
  valor original, undo/redo y truncado del redo, franja, descartar, `storage`,
  borrador/recuperación y commit. Repetible si otro paso toca este fichero.

Verificado: `pytest datadesk` → **254 en verde**; suite completa **1270 en
verde** · catálogos recompilados y `--check` en verde · el test de i18n ahora
valida las formas plurales · 27 comprobaciones del arnés de JS en verde.

### ⏭ Siguiente: S15

Panel de revisión y commit por lotes: lista de cambios agrupada por serie y
sello con `antes → después`, confirmación explícita, y el post-commit (recarga o
poda) sobre el buffer de S14.

