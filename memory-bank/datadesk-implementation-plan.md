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
| S15 | Panel de revisión + commit por lotes | S14 | M | sí | ✅ 2026-11-19 |
| S16 | `mode=new` completo (auto-numeración, fast row, bucle) | S11, S14 | L | **sí, tercer hito** | ✅ 2026-11-19 |
| S17 | Clonar serie + borrar con preview de dependencias | S12 | M | sí | ✅ 2026-11-19 |
| S18 | Crear un lookup desde el workspace | S12, S14 | M | sí | ✅ 2026-11-19 |
| S19 | Pantalla de lookups + merge | S7, S12 | M | sí | ✅ 2026-11-19 |
| S20 | Dashboard + colas "needs attention" | S8 | S | sí | ✅ 2026-11-19 |
| S21 | Activity log + revertir commit | S6, S12 | M | sí | ✅ 2026-11-19 |
| S22 | Teclado, i18n final, tests, limpieza | todas | M | sí | ✅ 2026-11-19 |

Leyenda de tamaño: XS < 1h · S ≈ medio día · M ≈ 1 día · L ≈ 2–3 días.

Hitos entregables: **S8** (ves tus datos), **S13** (puedes corregir un dato),
**S16** (puedes crear una serie), **S19+S21** (mantenimiento completo con red).

### Segunda tanda (tras la primera revisión de uso real)

S1–S22 cerraron el plan, y la primera revisión de la app en marcha dejó cinco
cosas. No van en un paso único porque son de tres naturalezas distintas: un bug
visual, un cambio de diseño, dos huecos funcionales que se dejaron fuera a
propósito y una puerta que existe pero no donde se busca.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S23 | El anillo del campo rechazado no se pierde | — | XS | sí (bug) | ✅ 2026-11-19 |
| S24 | Escala tipográfica y ritmo del interfaz | S23 | M | sí | ✅ 2026-11-19 |
| S25 | Borrar un sello con preview de dependencias | S17, S21 | M | sí | ✅ 2026-11-19 |
| S26 | Nueva fila en las tablas de referencia | S19 | S | sí | ✅ 2026-11-19 |
| S27 | Moverse entre series y borrar desde la lista | S15, S17 | M | sí | ✅ 2026-11-19 |

Orden: **S23** primero porque es el bug y toca el mismo CSS que S24; **S24**
después para no repintar dos veces. **S27** no depende de S25 ni de S26 y es lo
que se usa a diario —moverse entre series y quitar una fila sin abrirla—, así que
puede ir antes que ellos; **S25** y **S26** son huecos funcionales independientes
entre sí.

Lo que **no** entra en esta tanda, y sigue anotado en `progress.md`: corregir los
colores de un sello en `mode=edit` (necesita M2M en el change set).

### Tercera tanda (S28, pedida el 2026-11-20 — sin prisa)

Con DataDesk ya desplegado se preguntó si convenía meter Bootstrap o Materialize
para los controles, porque el interfaz «se siente anticuado». Se montaron tres
maquetas del mismo workbench con los mismos datos
(`memory-bank/mockups/workbench-compare.html`: actual, Bootstrap 5.3.3 y pulido
sobre los tokens de S24) y la comparación cerró el debate: no falta un framework,
faltan tipografía, estados y elevación.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S28 | Pulido visual: tipografía, controles y elevación | S24 | M | sí | ✅ 2026-11-21 |

---

### Cuarta tanda (S29–S32, tras la primera revisión con datos reales)

Cuatro cosas que se ven usando la app a diario, más un arreglo pequeño que salió
del panel de S29 (la placa de la imagen). No son de la misma naturaleza que S28:
aquella es piel, estas tocan datos, consultas y disco.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S29 | Ver la imagen y la descripción de un sello | — | M | sí | ✅ 2026-11-21 |
| S29b | La placa de la imagen del sello, que no sea blanca | S29 | XS | sí | ✅ 2026-11-22 |
| S30 | «Ver series afectadas» desde una tabla de referencia | S8, S19, S27 | S (3) / M (8) | sí | ✅ 2026-11-21 |
| S31 | Pantalla de backups: listar, lanzar, descargar | S15 | S | sí | ⏳ pendiente |
| S32 | Restore con mantenimiento, dump previo y secuencias | S31 | M | sí, pero es el botón rojo | ⏳ pendiente |

Orden: **S29 → S30 → S31 → S32**. S29 es la que más se nota usando la app; S32 la
última y solo si de verdad se quiere, porque es la única que puede destruir más de
lo que arregla.

Relación con S28: sin dependencia dura, pero S28 y S29 tocan el mismo
`datadesk.css` y la misma pantalla. Si se hacen las dos, **S28 primero** para no
repintar dos veces; S29 puede ir delante sin romper nada (S28 es solo CSS sobre los
mismos nombres de clase).

---

### Quinta tanda (S33, la operación que falta)

No viene de una revisión de estilo: viene de intentar hacer el trabajo. DataDesk
sabía crear una serie con sus sellos, clonar una serie entera y borrar un sello,
pero no **añadir un sello a una serie que ya existe**, que es lo que se hace cada
vez que llega una pieza suelta. El backend ya lo aceptaba; faltaba la pantalla, y
está hecha.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S33 | Añadir un sello a una serie existente | S15, S16, S25 | M | sí | ✅ 2026-11-22 |

---

### Sexta tanda (S34, vista la app en el servidor — no urgente)

Sale de mirar tres pantallas de la instancia de producción con datos reales. No
rompe nada y se puede trabajar con ello, pero hay un número que **miente** (el
total del pie del workbench), otro que **no se lee** (el dinero sin separadores, y
recortado con puntos suspensivos) y la misma cifra escrita de tres formas
distintas. Es deuda de presentación, no de datos.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S34 | El dinero, las fechas y el total del pie dicen lo que son | S8, S24, S28 | S–M | sí, aunque no es urgente | ⏳ pendiente |

---

### Séptima tanda (S35, los colores del sello)

El hueco que la app arrastraba desde S18: en `mode=edit` la celda de colores era
de lectura porque el change set no llevaba M2M, y corregir un color necesitaba
pasar por el admin de Django. El backend ya lo hacía entero: `/apply` acepta
`colors` en un `update` (`_colors_of` los saca del patch y `_update_row` hace
`set()`), el snapshot de S6 guarda los ids y el revert los devuelve. Lo que
faltaba era la puerta, y está en el panel de la imagen de S29: los colores se ven
al lado de la foto que los tiene.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S35 | Cambiar los colores de un sello desde el panel de la imagen | S18, S19, S29, S33 | M | sí | ✅ 2026-11-22 |

---

### Octava tanda (S36, el orden dentro de una fecha)

Reportado al usar la lista: dos series con la misma fecha no siempre salían en el
mismo orden. No es cosmético — el orden no era **total** (dos series podían
empatar en año, fecha y nombre), así que la base decidía, y con paginación por
`OFFSET` eso puede enseñar una fila dos veces y no enseñar otra. En los datos
reales hay **419 fechas repetidas** (955 series), y la mayor es el 29-12-1998 con
**15 series llamadas «España 2000»**.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S36 | El orden de la lista lo decide el código de la serie | S7, S8, S9 | S | sí | ✅ 2026-11-22 |

---

### Novena tanda (S37, el look de los controles)

Un detalle de piel con una causa de fondo: el aspecto de un control estaba
declarado **dentro de `.dd-field`**, así que el mismo `.dd-input` fuera de una
etiqueta —los campos del panel de la imagen— se pintaba como un control del
navegador. Se vio al poner el campo de color al lado de la tira.

| ID | Paso | Depende de | Tamaño | Deja algo usable | Estado |
|---|---|---|---|---|---|
| S37 | Un control tiene el mismo aspecto en cualquier sitio | S24, S28, S29, S35 | XS | sí | ✅ 2026-11-22 |

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
  copia. **La copia es una copia**: los valores se leen de las filas, no de un
  formulario, así que un hueco del origen (un sello sin valor facial, un sello
  sin color) viaja tal cual — arreglarlo es justo para lo que se clona. El
  nombre y los códigos también se copian: renombrar es una decisión del usuario
  y la copia se abre para que la tome; inventar «(copia)» metería en el catálogo
  una cadena que nadie eligió.
- `GET /datadesk/issues/<pk>/dependencies`: preview server-side con el número de
  sellos, de `CollectionItem` afectados y de colecciones de usuario, más la
  frase que el diálogo muestra (una sola frase, sin plurales: los números van
  aparte, en su propia lista).
- `POST /datadesk/issues/<pk>/delete`: confirmación escribiendo el año,
  comparada en el servidor, no en el navegador. **Cuenta otra vez dentro de la
  transacción**: el preview de la pantalla puede tener minutos, y un número que
  creció es peor que ningún número.
- Ambas acciones auditadas: el clon escribe `operation="create"` con
  `cloned_from` en el `after` de la serie (procedencia, no campo: solo aparece
  en filas `create`, y el revert de S21 borra lo que creó un `create` en vez de
  reconstruirlo, así que la clave nunca llega a `Model(**snapshot)`); el borrado
  escribe una fila por sello y otra por la serie con el `before` completo, que es
  de donde S21 reconstruye con los ids originales.
- Interfaz en la franja de la serie de `mode=edit`: `Clone` y `Delete`, las dos
  **desactivadas mientras el buffer tenga cambios** (una copia se hace de la
  base y un borrado ignora la pantalla: ninguna de las dos puede convivir con
  ediciones sin confirmar). El borrado abre un diálogo con los tres números y
  la caja del año; `Esc` lo cierra sin salir de la página.

**Aceptación**: clonar 8 sellos mantiene colores y `edifil`; borrar una serie
con `CollectionItem` avisa del número exacto y no borra si el texto no coincide;
sin `CollectionItem` el preview lo dice explícitamente. Probado también con la
serie de 57 sellos: el preview cuenta los 57 y la confirmación por año no cambia.

---

### S18 — Crear un lookup desde el workspace

**Depende de**: S12, S14.

**Corrección de partida**: el plan decía «celdas de lookup del grid», pero tras
la revisión del esquema un sello no guarda ningún atributo de la serie: los
lookups viven en la franja (`country`, `stamp_type`, `print_type`, `printer`,
`artist`, `paper_type`) y el único lookup del grid son los colores. Así que el
paso convierte **los seis campos de la franja** en campos tecleados con
sugerencias, y da al editor de colores la misma capacidad de crear.

- `GET /datadesk/lookups/<key>/search?q=` — búsqueda en el servidor sobre el
  registro (`icontains` sobre la columna que identifica la fila, ordenada por
  ella, 50 filas como máximo). Es lo que evita mandar la tabla entera con cada
  serie: los colores son 300 filas y los artistas 92 en los datos reales.
- El campo es un `<input list>` con `<datalist>`: el navegador filtra solo y el
  `accept` de siempre sigue funcionando, sin menú propio que mantener. El valor
  del formulario es el **id** y lo que se ve es el **nombre**; dos mapas
  (`id→nombre`, `nombre→id`) hacen de diccionario, sembrados con lo que la
  página pinta y ampliados con cada búsqueda y cada fila creada.
- `+ Crear "X"` aparece solo cuando el texto no es ninguna fila conocida: un
  botón permanente invita a duplicar lo que ya está elegido. El `POST` usa el
  endpoint de S12 (`get_or_create`), así que un nombre repetido devuelve la fila
  existente con `created: false` en vez de un 500.
- Un nombre tecleado que no existe **no se puede enviar** (el formulario habla
  ids): confirmar lo rechaza, marca el campo y dice qué hacer. Sin eso, `""` en
  una FK nullable habría borrado el valor en silencio.
- En `mode=new` el editor de colores es la lista de Tabulator, que no acepta
  texto libre: el color se crea desde el botón `New colour` de la barra del grid
  y entra en la lista que la celda ofrecerá la próxima vez que se abra. Crear un
  color no es ponerlo en un sello: elegirlo sigue siendo editar la celda.
- En `mode=edit` la fila creada **no es un cambio** (ya está escrita y auditada
  por el endpoint), así que el panel de revisión la muestra en su propio grupo,
  «New reference rows», con la frase que explica que se conserva. El botón
  `Review changes` se abre también cuando solo hay filas de esas.

**Aceptación**: crear un artista nuevo desde un campo y verlo en las sugerencias
de otra serie sin recargar; nombre duplicado → mensaje claro, no 500; la fila
creada aparece en el panel de revisión con su etiqueta.

---

### S19 — Pantalla de lookups y merge

**Depende de**: S7, S12.

Las ocho tablas de lookup entran en DataDesk (`ConditionType` se queda en el
admin porque solo la usan las colecciones de usuario) y comparten **una**
plantilla, un grid y cuatro operaciones, porque `registry.py` ya describe cada
una: modelo, columna que la nombra y relaciones que apuntan a ella.

- `/datadesk/lookups/` indexa las ocho con su número de filas; `/datadesk/
  lookups/<key>/` es el grid, con pestañas para las demás.
- **Contadores de uso anotados**: un `Count` por relación, con el accesor inverso
  sacado del campo del modelo (`Issue.artist` ya dice `issues`), `distinct=True`
  y sumados en Python. Una página de 50 filas cuesta **dos** consultas (el
  `count` de la paginación y la página), nunca una por fila.
- **Renombrar** inline; un nombre que ya existe devuelve **409
  `{error: "duplicate_name", existing_id, existing_name}`** y la pantalla abre el
  diálogo de fusión: la fila editada es el origen y la que ya tenía el nombre es
  la que se queda. Es lo que el usuario quería el 90% de las veces.
- **Fusionar** (`POST /datadesk/lookups/merge`,
  `{table, from_id, to_id, keep_name_from: "a"|"b"}`) en una transacción, con un
  diálogo que enseña las dos filas y **deja elegir qué nombre se queda** (`a` =
  el de la que sobrevive, `b` = el de la que desaparece), así el caso «el bueno
  es el de la otra» no obliga a renombrar antes:
  - **FKs**: un `update(fk=to)` y `updated_at` explícito, porque `auto_now` no se
    dispara con `update()` y el chequeo de conflicto de S12 se quedaría ciego.
  - **`colors` (M2M)**: un sello puede tener los dos colores, así que se rellena
    la tabla intermedia par a par (`bulk_create(..., ignore_conflicts=True)`) y
    después se borran las filas del color origen. Sin duplicados y sin depender
    de que `.add()` ignore conflictos, que cambió entre versiones de Django. Los
    sellos afectados reciben también su `updated_at`.
  - **`year`**: como un FK — la cascada no se dispara porque se mueven las series
    con un `update()`, no se borran.
  - Orden con `keep_name_from="b"`: mover referencias → borrar el origen (eso
    libera su nombre `unique`) → renombrar el superviviente. Al revés choca.
  - Auditoría: **una** fila `operation="merge"` con `before={lookup, refs}` y
    `after={lookup, refs}`, no 143 filas de ruido. No es reversible (S21 lo
    rechazará) y el diálogo lo dice antes de confirmar.
- **Borrar** solo si `usage == 0`; con uso responde 409 `{error: "in_use",
  usage}` y el grid ni siquiera pinta el botón, pinta el motivo.
- **`Year`**: acción «crear los 10 años siguientes» con `get_or_create` en bucle,
  sin auditar (el `Year` implícito de S12 tampoco se audita).

**Aceptación**: fusionar dos artistas mueve exactamente N referencias, deja 0
filas apuntando al origen y borra el origen; fusionar dos colores donde un sello
tiene ambos deja **una** fila en la tabla intermedia y ninguna duplicada;
fusionar años mueve las series; `keep_name_from="b"` deja el nombre del origen en
el registro superviviente y no choca con `unique`; renombrar a un nombre
existente devuelve 409 con el id del existente; borrar un lookup con uso devuelve
409; el contador del grid coincide con el número real de referencias; todo queda
en auditoría y un commit con `merge` queda marcado como no reversible.

---

### S20 — Dashboard y colas

**Depende de**: S8.

`/datadesk/` deja de ser la página provisional de S1 y enseña las seis colas de
`missing_data_report()`, cada una como una puerta al workbench con su filtro ya
puesto.

- **Una tabla de nombres, no tres**: `service.QUEUES` empareja el contador del
  informe (`issues_without_country`) con el filtro del workbench (`no_country`),
  su etiqueta traducida y la **unidad** de lo que cuenta. Un test comprueba que
  hay exactamente una cola por contador y que todos los filtros existen, así que
  un contador nuevo no puede quedarse sin tarjeta.
- **Tres colas cuentan sellos y el workbench filtra series**: la tarjeta de un
  contador de sellos lleva **los dos números** («1.177 · en 1.044 series»),
  porque la rejilla que abre cuenta series y una tarjeta que dijera 1.177 delante
  de una rejilla de 1.044 parecería un fallo. El número de series sale de
  `filter_issues()`, la misma función que usa el workbench: no pueden discrepar.
- **Contadores a cero**: no desaparecen ni se pintan como trabajo. Se listan
  aparte («Aquí no falta nada: …») y, si los seis están a cero, la página lo dice
  en lugar de enseñar seis tarjetas vacías.
- **Números formateados por idioma** (`number_format`): 1.177 en español, 1,177
  en inglés, sin que la plantilla lo sepa.
- Totales de series y sellos, y enlaces al workbench, a una serie nueva y a las
  tablas de referencia.

**Bug encontrado y cerrado aquí**: el filtro `stamps_without_image` del workbench
seguía mirando `Stamp.image` —columna **vacía en las 9.560 filas reales—**
mientras el contador ya contaba archivos desde S10b. En los datos reales ese
filtro devolvía **2.542 de 2.543 series**: «todo», y nadie lo había notado porque
los tests de S8 usaban la columna. Ahora las dos preguntas se responden con la
misma función, `picture_gaps()`, que devuelve el número de sellos sin imagen y
**el conjunto de series que los contienen** en un solo recorrido del índice
(1.177 sellos en 1.044 series, **28 ms** con el índice cacheado).

**Aceptación**: los números del dashboard coinciden con un recuento directo y con
el total del workbench filtrado (las tres colas de series de forma exacta, las de
sellos con su par series/sellos); cada tarjeta abre el workbench con su filtro
aplicado en la URL; un hueco arreglado baja el contador en la siguiente carga; y
una base completa lo dice en vez de enseñar ceros como trabajo.

---

### S21 — Activity y revertir

**Depende de**: S6, S12 (y del formato de auditoría de S19).

- `/datadesk/activity/`: commits en orden inverso, **paginados por commit, no por
  fila** (un lote de 40 filas es una decisión), cada uno con cuándo, quién,
  cuántos objetos y cuáles, la operación y **los campos que cambiaron**. Cada
  grupo lleva su estado: `reversible`, `no reversible: contiene una fusión`, o
  `revertido el …`.
- `POST /datadesk/activity/<commit_id>/revert`: **el commit entero o nada**, en
  una transacción, con vista previa en el diálogo (qué se hará con cada fila) y
  rechazo con motivo (409) si no se puede.
- Reglas por operación, y **el orden es parte de la regla**:
  - `create` → se borra lo creado, **hijos antes que padres** (una serie y sus
    sellos son filas del mismo commit: primero los sellos), porque al revés la
    cascada se lleva filas cuyo revert aún no ha corrido.
  - `update` → se escribe el **`before` completo**, no un diff, y `updated_at` a
    mano: `auto_now` no se dispara con `update()` y el chequeo de conflicto de
    S12 se quedaría leyendo un timestamp que no se movió.
  - `delete` → se recrea con el **id original** (`Model(id=…, **before)`), padres
    antes que hijos, con sus FKs, fechas, decimales y colores (la lista de ids
    de la M2M).
  - `merge` → rechazado: el commit entero es no reversible y el botón ni se
    pinta.
- Se rechaza (409, sin aplicar nada) si: el commit ya se revirtió, contiene una
  fusión, un objeto cambió después del commit (`updated_at` posterior), o al
  recrear choca (id ocupado, nombre `unique` en uso).
- **Lo que el revert no puede devolver**, y el diálogo lo dice: los
  `CollectionItem` que la cascada borró con una serie o un sello. Vuelve el
  catálogo, no quién tenía esos sellos.
- El revert **se audita como un commit nuevo**: sus filas llevan
  `reverts_commit_id` y las originales quedan con `reverted_at`, que es lo que la
  pantalla lee para decir «revertido el …» y no volver a ofrecer el botón.

**Aceptación**: revertir un commit de 5 cambios deja la base como estaba;
revertir un alta de serie la borra con sus sellos; revertir un borrado recrea
serie y sellos con sus ids y colores originales; un segundo revert del mismo
commit → 409 «ya revertido»; un objeto modificado después → 409 con el objeto;
un commit con `merge` → 409 y sigue siendo no reversible; recrear chocando con
un id ocupado → 409 en vez de un 500; el revert deja sus filas con
`reverts_commit_id` y las originales con `reverted_at`.

---

### S22 — Cierre

**Depende de**: todas.

Lo que faltaba no era funcionalidad sino lo que hace usable una app que no
escribió quien la va a usar:

- **Contrato de teclado completo**: `/` lleva al buscador (workbench y tablas de
  referencia), `j`/`k` mueven la selección, `N` abre una serie nueva; se suman a
  los que ya había (`Enter`, `Shift+Enter`, `Ctrl+Enter`, `Ctrl+D`, `Ctrl+Z`, `Esc`,
  `Tab`). Ninguna tecla dispara cuando el foco está en un control, y cada grid
  lleva debajo una línea que dice qué entiende: un atajo que nadie encuentra no es
  un atajo.
- **Barrido de i18n**: un test recorre `datadesk/static/datadesk/*.js` y falla si
  aparece prosa en un sitio donde se pinta texto (`textContent`, `title`,
  `placeholder`, `alt`). Los glifos que el script sí puede tener (`×`, `→`, `·`)
  quedan fuera por definición: no tienen dos palabras seguidas.
- **Accesibilidad**: `:focus-visible` en enlaces, botones y `summary` (antes solo
  los inputs tenían anillo), blanco sobre la barra oscura, `role="dialog"` en el
  panel de revisión, y `--dd-soft` oscurecido de `#9aa2ab` (2,6:1) a `#6b7280`
  (4,8:1) porque era el texto atenuado el que no pasaba AA.
- **Tests**: la cobertura de `datadesk/service.py` era del 99% y lo único que
  faltaba era la rama `sort == "date"` de `sort_issues` — ordenar el workbench
  por fecha no tenía test. Ahora sí (ascendente y descendente, nulos al final) y
  el módulo queda al **100%**; `datadesk` entero, al **98%**.
- **README** (el del repositorio, que ya tenía la sección de DataDesk; no un
  segundo documento): tabla de teclado, **backup antes de un commit grande**
  (el botón del panel y el comando), **cómo apagar DataDesk**
  (`DATADESK_ENABLED=False` desmonta la ruta, no toca datos) y **qué no devuelve
  un revert** (los `CollectionItem` que se llevó la cascada). La receta de
  allowlist por IP ya estaba.

**Aceptación**: `pytest backend/datadesk` en verde dentro del runner de backend;
`manage.py check --deploy` sin nuevos avisos atribuibles a DataDesk (los 6 que
salen son del proyecto y del entorno: HSTS, redirección SSL, `SECRET_KEY`,
`DEBUG` y las dos cookies seguras, que son justo lo que `DATADESK_TLS` pone en
producción).

**Fuera de este paso, y anotado, no supuesto**: los colores de un sello siguen sin
poder corregirse en `mode=edit` (el change set no lleva M2M) — está en
`progress.md` como hueco conocido.

---

### S23 — El anillo del campo rechazado no se pierde

**Depende de**: —

**Bug de S16.** Con varios sellos en el grid, el resalte de un campo rechazado se
ve a los lados y arriba, pero **no por abajo**: la fila siguiente lo tapa.

- Causa: `.dd-cell-invalid` pinta el anillo con `box-shadow: inset`, y la fila
  siguiente se pinta **después** con fondo opaco, comiéndose el borde inferior.
- Arreglo: que la celda marcada se pinte por encima (`position: relative` +
  `z-index`) o cambiar el anillo por un `outline` con offset negativo. Se prueba
  con la serie de varios sellos, no con uno.
- Revisar el mismo patrón en la franja (`.dd-input-invalid`): ahí los campos no
  se solapan, así que debería estar bien, pero se comprueba.

**Aceptación**: en una serie de tres sellos, el campo rechazado muestra el anillo
completo por los cuatro lados, incluida la fila que tiene otra debajo; el arnés
sigue comprobando que se pone la clase (el JS no cambia).

**Tamaño**: XS · `datadesk.css`.

**Hecho (2026-11-19)**: el anillo se queda dentro de la celda y se levanta con
`position: relative` + `z-index: 2` (3 dentro de una fila marcada). Se descartó el
`outline` con offset: el `outline` se pinta con la propia celda y la fila
siguiente lo tapa igual, porque el problema es el orden de pintado, no el borde.
Las filas de Tabulator son `position: relative` **sin** `z-index`, así que no
crean contexto de apilamiento y la celda sube por encima de la de abajo. Se
añadieron dos tests que fijan la declaración para que un pase de limpieza no se
lleve la línea que hace visible el anillo (el bug de pintado en sí se verifica a
ojo, con una serie de varios sellos). 2 tests; 443 datadesk y 1459 backend en
verde; arneses sin cambios.

---

### S24 — Escala tipográfica y ritmo del interfaz

**Depende de**: S23.

**Lo que se vio**: el interfaz «se siente anticuado». No es la paleta: es que
**nada pasa de 12,5 px** (16 usos a 12, siete a 10,5, dos a 9,5), las etiquetas
van en mayúsculas diminutas, la densidad es alta y el grid conserva el cromo por
defecto de Tabulator.

- **Escala**: base 14 px; celdas y campos 13; pistas 12; micro-etiquetas en
  mayúsculas 10,5 y **nada por debajo**. Interlineado acorde.
- **Ritmo**: escala de espaciado 4/8, alto de fila del grid 34 → 38, bordes más
  suaves y un único peso de separador.
- **Jerarquía**: dashboard y cabeceras de pantalla con un título legible; la barra
  de herramientas deja de ser seis controles del mismo peso.
- **Cromo de Tabulator**: cabecera con peso y fondo propios, filas alternas
  sutiles, hover que no compita con la fila seleccionada.
- El contraste se vuelve a medir con los tamaños nuevos (`--dd-soft` está en
  4,8:1 y no debe empeorar).

**Aceptación**: no queda ningún `font-size` por debajo de **11 px** en la hoja de
estilos y **ninguno escrito a mano**: todos salen de un token. Cada pantalla
revisada a 1366×768 sin scroll horizontal (el grid del workbench pagina, que es
otra cosa); el grid sigue enseñando ~14 filas; no se pierde ninguna columna ni
información.

**Tamaño**: M · `datadesk.css` casi entero, `base.html`, `workbench.html`,
`dashboard.html`.

**Hecho (2026-11-19)**: la escala queda en seis tokens (`--dd-text-xl` 22,
`--dd-text-lg` 16, `--dd-text` 14, `--dd-text-sm` 13, `--dd-text-xs` 12,
`--dd-label` 11) y **las 52 reglas de `font-size` que había pasan por ellos**; el
cuerpo sube a 14/1,5, el grid a 13 con filas de 36 px y celdas de 7/10, y la
barra superior a 48. Lo que más cambia la sensación no es el tamaño: es que el
grid deja de llevar el cromo de Tabulator —`1px solid #aaa` en las celdas, cebra
`#efefef` y fila seleccionada `#9abcea`— y pasa a usar `--tabulator-border`
(`--dd-line`), cebra casi blanca, selección en azul grisáceo y hover que no
compite. La tarjeta de página pasa de borde `#d8dce1` y sombra de 28 px a borde
`--dd-line` y dos sombras de 2/24 px, y el título de pantalla es el último
migajón de pan a 16 px (evita añadir un `h1` que repita el mismo texto). Además:
las barras de commit y del workbench envuelven en vez de desbordar a 1366, el
panel de revisión pasa a 380 px para que los `antes → después` no bailen con el
texto nuevo, y los migajones truncan un nombre de serie largo en vez de empujar
la barra. Cuatro tests sujetan la escala: ningún `font-size` literal, todos desde
un token, ninguno por debajo de 11 y el cuerpo usando `--dd-text`. 4 tests; 447
datadesk y 1463 backend en verde; arneses sin cambios (no se tocó JavaScript).

**Remate del mismo paso, tras verlo en un 2560**: con la letra nueva el workbench
ya pedía scroll horizontal, así que la aceptación no se cumplía. Cuatro cosas:

- **La tarjeta pasa de 1340 a 1600 px**: a 2560 se queda centrada con aire en vez
  de estirarse, y a 1366 ocupa todo el ancho disponible.
- **El workbench y la tabla de lookups pasan a `fitColumns`**: las columnas se
  reparten el ancho de la tarjeta y **nunca** aparece barra horizontal, en vez de
  que Tabulator mida el contenido (`fitDataStretch`) y scrollee cuando un nombre
  es largo. Como `fitColumns` reparte a partes iguales si no se le dice otra cosa,
  cada columna declara su `grow` en las definiciones de `workbench.py` (nombre 4,
  país y clasificación 2, números 1) y el nombre lleva `minWidth: 180`; sin eso
  «Name» acabaría tan estrecha como «Stamps».
- **`text-decoration: none` en `.dd-btn`**: un `<a>` con clase de botón se
  subrayaba y un `<button>` no, así que el mismo control se veía distinto en el
  dashboard y dentro del workspace. S17 había tapado el síntoma con parches
  locales (`.dd-meta-actions a`, `.dd-meta-back`), que ahora sobran.
- La altura del grid del workbench baja a `calc(100vh - 300px)`: con la barra a 48
  y las filas a 36, el `-260px` hacía que la página entera scrolleara un poco.

Dos tests más (449 datadesk, 1465 backend): uno comprueba que toda columna visible
declara su parte del ancho y que el nombre es la mayor, otro que `.dd-btn` quita el
subrayado.

**Tercer remate, los botones**: no todos medían lo mismo ni centraban el texto.
La causa era la misma de antes, el `<a>` con clase de botón: su texto se alinea a
la línea base y su alto salía del padding, no de una caja. `.dd-btn` pasa a
`inline-flex` con `align-items`/`justify-content` centrados, **alto fijo**
(`--dd-btn-height: 32px`) y `padding: 0 14px`; `.dd-btn-ghost` sólo aprieta los lados (`0 10px`) y ya no
declara alto, así que un `Undo` al lado de un `Save` mide igual que él. Con
`line-height: 1` el texto deja de bailar según la variante. 3 tests en
`TestButtons` (subrayado, centrado y que el alto no dependa de la variante); 451
datadesk y 1467 backend en verde.

---

### S25 — Borrar un sello con preview de dependencias

**Depende de**: S17, S21.

**Lo que se vio**: no se puede borrar un sello de una serie existente. El change
set rechaza `delete` a propósito desde S12 (borrar sin preview se lleva los
`CollectionItem` de la cascada) y S17 solo lo resolvió para la serie.

- `GET /datadesk/stamps/<pk>/dependencies`: ítems de colección que se llevaría y
  en cuántas colecciones están, más la identidad del sello (edifil/fesofi y
  nombre) para que el diálogo diga qué se borra.
- `POST /datadesk/stamps/<pk>/delete`: una transacción, una fila de auditoría
  `delete` con el `before` completo (S21 lo recrea con su id y sus colores), y la
  cascada se lleva los `CollectionItem`, que **no** vuelven con el revert y el
  diálogo dice.
- **Sin confirmación tecleada**, a diferencia de la serie: una fila no es un
  conjunto, el diálogo la nombra y el preview dice el número. Decisión a validar.
- Interfaz: una acción por fila en `mode=edit` (el `×` de los borradores de S16
  ya existe en `mode=new`; se reutiliza el patrón), desactivada mientras el
  change set tenga cambios, y el diálogo con los números.
- El borrado **no entra en el buffer** (regla de S14): es un diálogo con su
  propia confirmación.

**Aceptación**: borrar un sello con ítems avisa del número exacto y lo borra;
sin ítems lo dice explícitamente; el revert de S21 lo devuelve con su id y sus
colores y **no** devuelve los `CollectionItem`; el botón no existe en `mode=new`
ni con cambios pendientes.

**Tamaño**: M · `datadesk/write.py`, `views/write_api.py`, `views/workspace.py`,
plantilla, JS, tests.

**Hecho (2026-11-19)**: `dependencies.stamp_dependencies()` (dos consultas: los
ítems de colección y los sellos hermanos) y `stamp_warning()` con sus cuatro
combinaciones —está o no en colecciones, es o no el último de la serie—;
`write.delete_stamp()` con una fila `delete` y el snapshot completo, que es lo
que S21 usa para devolverlo con su id y sus colores; `GET stamps/<pk>/dependencies`
y `POST stamps/<pk>/delete`. En el grid, una columna `×` en `mode=edit` con su
diálogo, **sin confirmación tecleada** (decisión confirmada: una fila no es un
conjunto) y atenuada mientras el change set tenga cambios, donde además el clic
se niega con el motivo. Cada fila lleva sus dos URLs en los datos, como la de la
imagen, para que el script no componga rutas. **20 tests** (los cuatro casos del
aviso, la cascada, la auditoría, el revert con id y colores pero sin
`CollectionItem`, los dos endpoints con su gate, que `/apply` sigue devolviendo
409 y que la rejilla de `mode=new` no tiene la acción) y **15 comprobaciones
nuevas** en el arnés de `mode=edit` (diálogo, preview, recuentos, frase,
identidad, POST, fila fuera, contador y bloqueo con cambios pendientes): 471
datadesk, 1487 backend y el arnés en 89.

---

### S26 — Nueva fila en las tablas de referencia

**Depende de**: S19.

**Lo que se vio**: las tablas auxiliares dejan renombrar, fusionar y borrar, pero
no **crear**. Se dejó fuera a propósito porque crear vive en el workspace con el
botón `+`, y con la pantalla delante la falta se nota.

- Botón `New row` en `/datadesk/lookups/<key>/`: diálogo con el nombre (numérico
  para los años, con los mismos límites que la franja) y el endpoint de creación
  que ya existe (`lookups/<key>/create`, `get_or_create`).
- Al crear: se recarga el grid y la fila nueva se resalta, en su posición
  ordenada. Un nombre repetido **selecciona la existente** y lo dice, en vez de
  fallar.
- El borrado sigue rechazándose con uso > 0 (la vía es fusionar) y la pantalla lo
  dice; crear no cambia esa regla.

**Aceptación**: crear un artista desde la pantalla y verlo en el grid sin
recargar a mano; un duplicado selecciona el que ya estaba; un año se valida como
número; la fila nueva se puede renombrar y borrar en el acto.

**Tamaño**: S · `views/lookups.py`, plantilla, `lookups.js`, tests.

**Hecho (2026-11-19)**: botón `New row` en la barra y `N` en el teclado, con un
diálogo de un solo campo —`type="number"` con los límites de `rules.series_year_bounds()`
cuando el lookup es numérico, y los mismos límites en la configuración— que usa el
endpoint de creación que ya existía (`get_or_create`, auditado, y por tanto
revertible por S21). Un duplicado devuelve `created: false` y la pantalla
**selecciona la fila que ya estaba** en vez de dar error. Como la rejilla ordena
por nombre, una fila nueva puede caer en otra página: tras crear se recarga y, si
no está en la página, se busca por su nombre y se resalta (`dd-row-flash`), que es
más honesto que teletransportar a la primera página con la fila fuera de la vista.
4 tests y 6 comprobaciones nuevas en el arnés de lookups (diálogo, POST, estado,
fila seleccionada, `N` y `Esc`): 475 datadesk, 1491 backend y el arnés en 12.

---

### S27 — Moverse entre series y borrar desde la lista

**Depende de**: S15, S17.

Dos cosas que se vieron usando la app, y las dos son «no me hagas volver a la
lista»: para pasar a la serie siguiente hay que salir, y para quitar una fila hay
que abrirla.

#### A. Anterior y siguiente dentro del workspace

El vecino **no es `id ± 1`**: es el siguiente de la lista del workbench, con los
filtros y el orden que tuvieras puestos. Pasar de una serie de 1987 sin país a
una de 1994 porque el id es consecutivo sería peor que no tener flechas.

- La maquinaria ya existe: `page_of_issue()` (S15) recorre la lista de **pks**
  con filtros y orden por defecto. Se extrae esa lista a una función compartida
  (`issue_positions(filters)`) y `neighbours_of_issue(pk, filters)` devuelve
  anterior, siguiente, posición y total, sin una consulta de más (`len(pks)` es el
  total). 2.540 enteros, unos 5 ms.
- **La vista de serie tiene que saber con qué filtros llegaste**: el `↗` y el
  `Enter` del workbench pasan la query en el enlace, y la vista la devuelve en las
  flechas, en el contador y en «Back to the issues workbench», que hoy va a
  `/datadesk/issues/` a secas y pierde el filtro (`Esc` sí lo conserva porque usa
  `history.back()`).
- Franja: `‹` `›` a la izquierda de Clone/Delete, contador discreto
  (`1.234 / 2.540`) y **desactivadas en los extremos**, sin dar la vuelta.
- Teclado: `[` y `]`. `j`/`k` no valen aquí —dentro del workspace son de las
  celdas— y `Alt+←` lo secuestra el navegador en algunos sistemas.
- Si la serie no está en el conjunto filtrado (enlace viejo, o se llegó desde el
  dashboard), se cae al orden sin filtros antes que dejar las flechas muertas.
- `mode=new` no pinta flechas: no hay vecinos.

#### B. Borrar la serie desde la fila del workbench

- Una acción de borrado por fila (o sobre la selección) que abre **el mismo
  diálogo de S17**: el preview (`GET issues/<pk>/dependencies`) y el POST ya
  existen; lo que falta es la puerta.
- Al confirmar: se recarga el grid y la fila desaparece; un banner dice qué se
  borró y cuántos sellos se fueron con ella.
- Teclado: `Supr` sobre la fila seleccionada **abre el diálogo**, nunca borra
  directamente.
- El botón del workspace se queda: esta es la segunda puerta, no una mudanza.

**Aceptación**: los filtros sobreviven a la ida y a la vuelta (la flecha lleva la
misma query y el botón de volver también); el contador coincide con el total del
workbench filtrado y las flechas están desactivadas en el primer y último
elemento; `[`/`]` no disparan con el foco en un campo; cambiar de serie con
cambios pendientes avisa (`beforeunload`) y el borrador por serie sigue ahí al
volver; borrar desde la lista pide el año igual que desde el workspace y borra lo
mismo; `Supr` solo abre el diálogo (comprobado en el arnés).

**Tamaño**: M · `service.py`, `views/workbench.py`, `views/workspace.py`,
plantillas, `issue_workspace.js`, `workbench.js`, tests.

**Hecho (2026-11-19)**: `issue_positions()` extrae la lista de pks que ya
recorría `page_of_issue()` y `neighbours_of_issue()` devuelve anterior, siguiente,
posición y total con esa misma consulta; `navigation_for()` construye las dos
rutas con la query de los filtros, el contador formateado y el enlace de vuelta, y
**cae al orden sin filtros** si la serie no está en el conjunto (enlace viejo o
llegada desde el dashboard). El `↗`/`Enter` del workbench llevan los filtros en el
enlace (`?attention=…`), que era la mitad del problema: sin eso la vista de serie
no sabía de dónde venías. Teclado `[`/`]` con guarda de campo. En el workbench, una
columna `×` con el **mismo diálogo** que el workspace —extraído a
`partials/series_delete_dialog.html` y compartido, para que la decisión se pregunte
igual en los dos sitios—, preview y POST que ya existían, banner al terminar y
`Supr` que **solo abre** el diálogo. Cada fila del JSON de la rejilla lleva sus dos
URLs, como las del sello. 13 tests (8 de vecinos y flechas, 5 de la rejilla y el
diálogo) y **15 comprobaciones nuevas** en los arneses (9 en el del workbench:
`Enter` con filtros, `Supr`, preview, recuentos, etiqueta del año, POST, cierre y
banner; 6 en el de `mode=edit`: `[`/`]` y sus guardas): 488 datadesk, 1504 backend.

---

### S28 — Pulido visual: tipografía, controles y elevación

**Depende de**: S24. **Pedido el 2026-11-20. Estado**: ✅ 2026-11-21.

Origen: la pregunta de si conviene Bootstrap o Materialize. La respuesta corta es
que no, y las tres maquetas del workbench lo argumentan solas.

- **Bootstrap** no quita lo anticuado, lo cambia por genérico: botón azul, `×`
  negras de `btn-close` en cada fila, tabla a 16px. Y no resuelve el problema que
  de verdad importa: la tabla se autoajusta, así que Year y Date se pegan y se
  leen como una celda. Para que la rejilla reparta anchos como la nuestra hay que
  escribir el mismo CSS de S24 que ya está escrito. Te da los controles, no el
  layout de tus datos.
- **Materialize** es Material 1 (2014), sin mantenimiento real y con jQuery de
  dependencia: sería más viejo, no menos.
- **Tailwind** queda fuera mientras no haya Node en el repo: exigiría meter un
  paso de build, y eso es una decisión de toolchain, no un cambio de CSS.

Los cinco cambios, todos sobre `datadesk.css` y sin tocar markup ni JS:

1. **Tipografía.** Inter variable self-hosted (~48 KB woff2 en
   `datadesk/static/datadesk/vendor/`, con su sha256 en `VERSIONS.md` como el
   resto de lo vendorizado) en lugar de `system-ui`, que cae en DejaVu o Liberation
   según la máquina. Es lo que más cambia la lectura de la pantalla.
2. **Controles.** Inputs de 34px, borde `--dd-line-strong`, estado hover, y foco
   con anillo suave (`box-shadow: 0 0 0 3px` al 12%) en vez del `outline` sólido
   con `offset: -1px` de hoy; chevron propio en los `select` (`appearance: none`).
3. **Movimiento.** 120ms en el hover y el foco de botones, filas, inputs y
   enlaces. Hoy no hay una sola transición en todo el CSS.
4. **Elevación.** Dos niveles (`--dd-shadow-rest` para lo que reposa,
   `--dd-shadow-float` para lo que flota), la tarjeta deja el borde de 1px, y la
   **cabecera de la rejilla pasa a clara** en vez de navy —la navy se queda en la
   topbar—. Es el cambio que más moderniza la pantalla.
5. **Ritmo.** Escala de espaciado de 4px, fila de 38px,
   `font-variant-numeric: tabular-nums` en las columnas numéricas y un `—` apagado
   en las celdas vacías, que hoy parecen un fallo de pintado.

**Aceptación**: la maqueta y la app se parecen; ningún `font-size` literal y nada
por debajo de 11px (los cuatro tests de la escala de S24 siguen verdes); el foco
se ve con teclado y no con ratón, y no lo tapa la fila siguiente (lo de S23);
contraste AA mantenido en `--dd-soft` y `--dd-muted`; ninguna dependencia nueva
salvo la fuente.

**Fuera de alcance, y por qué**: formatear importes y fechas por locale en la
rejilla es un formatter de JS o del servidor, no un skin; y el `?v=<mtime>` para
el cache-busting de estáticos sigue pendiente por su cuenta.

**Verificación**: el devcontainer tiene Chromium headless (playwright), así que
este paso se comprueba con capturas antes/después en vez de a ciegas —que es como
se hizo el mockup—.

**Tamaño**: M · `datadesk.css`, `vendor/` + `VERSIONS.md`, los tests de escala y
anillo, y las capturas.

---

### S29 — Ver la imagen y la descripción de un sello

**Depende de**: —. **Estado**: ✅ 2026-11-21.

**Lo que hay hoy (medido)**: la columna de imagen mide 64 px y la miniatura está
limitada a `max-height: 26px; max-width: 54px` dentro de filas de 38 px (S24) —a
ese tamaño no es una foto, es una muestra de color—. `Stamp.description` es un
`TextField(null=True, blank=True)` que **no se serializa en ningún sitio de
DataDesk**: `serialize_stamp()` no lo incluye y `STAMP_COLUMNS` no tiene columna.
Lo que la franja muestra como «Description» es `Issue.description`, que es otro
campo. `StampRequestSerializer` ya incluye `description`, así que el camino de
escritura lo acepta sin tocar backend, y `""` en columna nullable ya se convierte
en `None`.

**Decisión (cerrada al implementar, 2026-11-21)**: sin hover y sin clic sobre la
imagen, el mecanismo es un **panel a la derecha del grid** atado a la fila
seleccionada, con **`j`/`k` en el workspace** (no existían ahí: la selección
tampoco, así que S29 las añade) y **editable en los dos modos**:

1. **Panel de previsualización atado a la fila seleccionada.** No añade gesto
   nuevo. La selección existe en el workbench desde S10 pero **no en la pantalla
   de la serie**: `selectableRows` no estaba puesto y `j`/`k` eran del workbench.
   S29 pone `selectableRows: 1` y mueve la selección con `j`/`k`.
2. **Selector de tamaño S/M/L** (26/48/72 px) **descartado** en este paso: es una
   preferencia de densidad, no la solución, y con 57 sellos 72 px son ~4.000 px de
   scroll. Queda como posible paso posterior.

La descripción vive en una **columna oculta** (`visible: false`) con
`patch: "description"`: así entra en el change set, en el panel de revisión
(`Stamp description`, porque «Description» ya es la de la serie) y en el borrador
de `localStorage` sin maquinaria nueva, y seleccionar otro sello no pierde lo
escrito. El panel escribe en esa celda con los eventos silenciados (`quietCell`):
una pulsación no es un paso de undo, y el undo ya no se reengancha a sí mismo.
La celda `getOldValue()` es la del arranque de la página, no la que se edita, así
que la base se toma de `previewStart` (valor al enfocar).

**La placa de la imagen.** Los ficheros del árbol son **WebP RGBA con el sello
recortado** (alpha 0 en las esquinas), así que el fondo lo pone la pantalla. Y la
mayoría de los sellos llevan marco blanco o casi blanco: **sobre blanco el dentado
desaparece** y el sello se lee como un cuadrado. La imagen va sobre una placa gris
neutra con un hairline, nunca sobre `#fff`; hoy el panel pinta `background: #fff`
en `.dd-preview-image`, que es justo el caso malo. La miniatura de 26 px tiene el
mismo problema en menor escala, porque se apoya en la fila blanca. (Las mismas
imágenes las enseña la app pública de Flet, así que la regla vale también allí.)

**Diseño**: panel a la derecha del grid (debajo en pantallas estrechas) con la
imagen a tamaño real, nombre y código, y la descripción debajo. Se alimenta de la
fila seleccionada sin petición nueva: la imagen ya se sirve por
`/datadesk/stamps/<id>/image` con ETag y la fila ya trae `image_url`. Descripción
vacía: un `—` apagado, no un hueco. **La descripción se edita ahí** (textarea) y
entra en el change set como cualquier campo, con su `before → after` en el panel de
revisión. Etiqueta **«Stamp description»**, porque «Description» ya es la de la
serie en la franja. Las etiquetas vienen del config del servidor (test de S22).

**Aceptación**: la imagen se distingue sin hover ni clic sobre ella, y `j`/`k` la
cambian sin tocar el ratón; se apoya en una placa que no es blanca y el dentado se
distingue del fondo; la serie de 57 sellos se recorre sin scroll horizontal
a 1366 px y el alto de fila no cambia con el panel cerrado; la descripción se lee y
se guarda, aparece en la revisión con su `before → after` y se deshace con `Ctrl+Z`
como el resto; un sello sin descripción no finge tenerla; catálogos limpios
(`datadesk_make_messages --check`); los tests de escala de S24 y del anillo de S23
siguen verdes.

**Fuera de alcance**: subir o reemplazar imágenes (el árbol sigue siendo de solo
lectura), la descripción de la **serie** en el workbench (la fila es una serie, no
un sello), zoom/modal/galería.

**Tamaño**: M · `views/workspace.py`, `templates/datadesk/issue_workspace.html`,
`static/datadesk/issue_workspace.js`, `datadesk.css`, tests de workspace y el arnés
de `mode=edit`.

**Implementado (2026-11-21)**: panel a la derecha, `j`/`k` y columna oculta en los
dos modos; verificado en Chromium a 1366 px (imagen de 258 px de ancho, sin scroll
horizontal) y a 1024 px (el panel pasa debajo). Dos bugs **previos** aparecieron al
probarlo y se arreglaron aquí porque bloqueaban la comprobación: `mode=new` llamaba
`grid.setData()` en el mismo tick que construye Tabulator y reventaba con
`renderer ... verticalFillMode` (ahora espera a `tableBuilt`); y `?rows=N` no se
lee en ningún sitio de la vista, así que el control siempre enseña 4 (anotado en
`progress.md`, sin tocar en este paso).

---

### S30 — «Ver series afectadas» desde una tabla de referencia

**Depende de**: S8, S19, S27. **Estado**: ✅ 2026-11-21.

**Lo que hay hoy**: los filtros del workbench son `year_min`, `year_max`, `q`,
`country`, `stamp_type` y `attention`, así que solo 2 de los 8 lookups tienen
filtro. `lookup_page()` ya anota el uso por fila, así que el número que se
convertiría en enlace ya está calculado, sin consulta extra. Y S27 ya hace que las
flechas y `[`/`]` recorran **la lista filtrada**.

**Decisión**: el número de uso se convierte en enlace cuando es > 0 («38 series →»);
a 0, texto. El coste no está en la consulta sino en que **todo filtro activo se
pinte como chip con su botón de quitar**: si no, se aterriza en una lista filtrada
sin saber por qué ni cómo limpiarla. Ese chip es el trabajo real.

| Lookup | Cómo se filtra | Coste |
|---|---|---|
| `year` | `year_min=N&year_max=N` | gratis |
| `country` | `country=<id>` | gratis |
| `stamp_type` | `stamp_type=<id>` | gratis |
| `printer`, `artist`, `paper_type`, `print_type` | campos nuevos en `IssueFilters` + condiciones en `filter_issues` | S, pero necesita el chip |
| `color` | `stamps__colors=<id>` con `distinct` | M, y cuidado con el número |

**La trampa del color**: la tabla de lookups cuenta **sellos** y la rejilla cuenta
**series** (en imágenes, 1.177 sellos en 1.044 series), así que el enlace no puede
decir «1.177 series». El texto dice la unidad que va a enseñar la rejilla y el
número sale de un `Count` de series, no del contador de uso.

**Aceptación**: un lookup con uso > 0 lleva a la lista y el contador del workbench
coincide con el número del enlace; uso 0, sin enlace; cada filtro de la URL se ve
como chip, se quita de uno en uno y sobrevive a paginar, ordenar y abrir una serie;
el chip de color dice «series» y el número es de series; las flechas de S27 y
`[`/`]` recorren el resultado.

**Fuera de alcance**: filtros guardados o con nombre, filtros multivalor.

**Tamaño**: S con los tres gratis, M con los ocho (recomendado: los ocho de una
vez, porque el chip se escribe igual) · `service.py`, `views/workbench.py`,
`views/lookups.py`, plantillas de workbench y lookups, `workbench.js`, `lookups.js`,
tests.

**Implementado (2026-11-21)**, con tres correcciones al plan:

- **El color va con `Exists`, no con `stamps__colors` + `distinct`**: el propio
  `service.py` documenta que un join multiplica filas y rompe el `Count("stamps")`
  del grid. Hay un test con un sello de dos colores que comprueba que la serie
  sigue contando 1 sello.
- **Los chips se pintan en el script, no en el servidor.** El formulario actualiza
  la URL con `replaceState` y recarga solo el grid; unos chips renderizados por
  Django se quedaban viejos al cambiar un filtro desde la propia barra (se vio en
  el navegador: `?printer=11` con la lista filtrada y sin chip). Ahora salen del
  formulario, con las etiquetas traducidas en el config, así que chips y grid no
  pueden discrepar. Primera pintura incluida.
- **`filters_from()` es una sola función**, en `views/workbench.py`, y
  `workbench_api.py` la importa: el endpoint del grid tenía su propia copia del
  parser y los cinco filtros nuevos se habrían quedado solo en la página.
  `IssueFilters.FILTER_NAMES` y `FILTER_FIELDS` son la lista única, y el config le
  pasa `filterNames` al script para que la URL no pierda ninguno.
- El enlace de un año usa `year_min` **y** `year_max` con el número del año (el id
  de `Year` no es el año), y `filter_url` viaja por fila para que el script no
  componga la URL.
- El color anota `Count("stamps__issue", distinct=True)` en la misma consulta: la
  columna dice **series** («40 series») y el `title` de la celda sigue diciendo los
  sellos («Used by 50 rows») cuando los dos números difieren.

**Revisión tras usarlo (2026-11-21, mismo día)**, con dos cosas que no salieron en
las pruebas:

- **El grid se salía de la pantalla.** Añadir cinco `select` dejó la barra en cuatro
  filas (193 px) y el grid seguía con `height: calc(100vh - 300px)`, un número que
  S24 había ajustado a una barra de dos filas: en 1440×900 el pie con la paginación
  quedaba en y=899, justo fuera. Ahora `.dd-workbench-page` es una columna tan alta
  como la ventana y el grid toma lo que dejan los filtros (`flex: 1`, `height:
  100%`), así que el pie está siempre dentro por muy alta que sea la barra. De paso:
  `[hidden]` no ocultaba la fila de chips vacía porque `display: flex` pisaba el
  atributo, y la regla `[hidden] { display: none !important }` lo arregla para todos.
- **Los cinco filtros nuevos van detrás de «More filters»** (un `<details>`, sin
  JS), y se abren solos cuando uno de ellos está filtrando; la barra vuelve a medir
  104 px en reposo. Alternativa descartada: quitarlos y filtrar solo desde las tablas
  de referencia.
- **La capa de servicio no compone URLs.** `lookup_page()` construía el enlace de
  cada fila con `reverse("datadesk:issues")`, y ese namespace solo existe con la
  app montada: en CI, con `DATADESK_ENABLED` apagado, los catorce tests que llaman
  al servicio directamente morían con `NoReverseMatch` (`test_lookups` y el revert
  de un rename en `test_activity`). Ahora el servicio devuelve `filter: {...}` y la
  vista compone el `filter_url` (`with_filter_url()`), como ya hacía el workbench
  con las URLs de sus filas. Y `pytest.ini` fija `DATADESK_ENABLED=False`, así que
  los tests corren siempre sin montar —como CI— y `mounted` la enciende donde toca:
  un `reverse` en el servicio falla en local en vez de en la pipeline.
- **El episodio del script viejo**: «los filtros no funcionan» resultó ser el
  `workbench.js` anterior en el navegador. Los `select` los pinta el servidor y los
  lee el script, así que la página enseñaba los filtros nuevos y no filtraba nada —
  la URL sí llevaba el parámetro. Ahora los assets de DataDesk llevan `?v=` con la
  fecha del fichero más nuevo (`datadesk/context.py`, context processor), así que el
  navegador vuelve a pedirlos en cuanto algo cambia; en producción el manifiesto ya
  los hashea y el sello no estorba. Comprobación para el futuro: si vuelve a pasar,
  mirar si `workbench.js` servido contiene `paintChips`.

---

### S31 — Pantalla de backups

**Depende de**: S15.

**Lo que hay hoy**: `POST /datadesk/backup` ya llama a `stamps_db_backup` en modo
`stamps` con nombre `datadesk-YYYYmmdd-HHMMSS`, y se ofrece a partir de 20 cambios;
ese camino se queda como está. Los comandos hacen backups **completos** por grupos
(`system`, `stamps`, `full`) y lo mismo para el restore. Tamaño real:
`latest__stamps.json` = **11,6 MB / 12.763 objetos**; el de sistema, **24 KB /
126 objetos**. `BACKUP_DIR = BASE_DIR/backups`, **dentro del contenedor**: sin
volumen, los dumps mueren en el próximo despliegue.

**Decisión**: el backup ya existe; falta el sitio. Pantalla `/datadesk/backups/`
que lista lo que hay, deja lanzar uno eligiendo modo y **descargar**. Sin descarga
es teatro: 11,6 MB se bajan sin problema y es la única salida real si no hay
volumen montado.

**Diseño**: lista con nombre, modo, tamaño y fecha, lo más nuevo primero (se
reutiliza el criterio de `_list_backups`); lanzar con nombre generado o escrito,
con la validación de caracteres del comando, y modo `stamps` o `full`; descargar
con `FileResponse`, `staff` obligatorio y el nombre **resuelto contra el listado
del directorio**, nunca concatenado desde la entrada (path traversal); estado vacío
honesto y una línea que diga dónde viven los ficheros. README: o volumen en el
compose de producción, o los backups solo sirven hasta el siguiente deploy.

**Aceptación**: se ve lo que hay, se lanza uno y aparece en la lista sin recargar a
mano; la descarga devuelve el JSON correcto y un nombre inventado da 404, no un
fichero de fuera del directorio; un usuario no staff no llega ni a la lista ni a la
descarga; el botón del panel de revisión (S15) sigue funcionando igual.

**Fuera de alcance**: retención o purga automática, backups programados (eso es
cron en el host).

**Tamaño**: S · `views/`, `urls.py`, plantilla nueva, navegación, tests.

---

### S32 — Restore: mantenimiento, dump previo y secuencias

**Depende de**: S31.

**Lo que hay hoy (verificado)**: `stamps_db_restore` es **`loaddata` y nada más**,
sin `flush` y sin reset de secuencias. `loaddata` con una PK que ya existe hace
**UPDATE**, no insert: sobrescribe. Pero **no borra lo que no está en el dump**, así
que las filas creadas después del backup sobreviven, y el resultado no es «la base
como estaba» sino «el dump manda en las filas que ya existían, y lo nuevo se
queda». `stamps_clear_data` hace `TRUNCATE ... RESTART IDENTITY CASCADE` y deja las
secuencias en 1; `loaddata` inserta ids explícitos y **no las avanza**, así que
encadenar las dos deja la secuencia en 1 y el siguiente sello que se cree intenta
id=1 → `duplicate key`. La solución es `manage.py sqlsequencereset`. `users_api` es
autocontenida (sin FK a `auth.User`), así que `stamps` no depende de `system`; y
`system` incluye `sessions` y `rest_framework_api_key`, o sea que restaurarlo
resucita sesiones cerradas y una API key revocada.

**Decisión**: el restore no compite con S21, lo complementa — el revert deshace
**un commit** con precisión; el restore es para cuando el destrozo no está en el
log (un `loaddata` por SSH, un script, un merge)—. Viven en sitios distintos: el
revert en la actividad, el restore en la pantalla de backups, que se visita poco.
Se implementa con tres cosas, y sin las tres no se implementa:

1. **Secuencia completa**: dump automático `pre-restore-<ts>` → modo mantenimiento
   → `clear_data` + `loaddata` + `sqlsequencereset` → mantenimiento off.
2. **Confirmación tecleada** con el nombre del fichero, el número de objetos y lo
   que va a desaparecer. No un «¿seguro?».
3. **Modo mantenimiento** de verdad: mientras está activo, todo `/datadesk/` menos
   la pantalla de restore (y el login) responde 503. Con 4 workers de gunicorn y sin
   cerrojo, un restore concurrente deja la base a medias y el `TRUNCATE CASCADE` no
   perdona.

En el panel solo `stamps` y `full`; `system` se queda en la CLI, donde sabes lo que
haces. `full` lleva una línea explícita de lo que trae de vuelta (sesiones y API
keys); el caso normal, deshacer un destrozo de datos, es `stamps`.

**Aceptación**: restaurar sobre la misma base deja los datos del dump y el
siguiente sello creado no colisiona (secuencias al día); sobre una base recién
migrada también, que es el caso que hoy rompería; antes de tocar nada se escribe el
`pre-restore-...` y la pantalla dice cuál es para poder volver; mientras dura, el
resto de `/datadesk/` da 503 y al terminar se apaga solo; un fallo a mitad deja el
mantenimiento **encendido** y nombra el dump previo; el diálogo no deja continuar
sin escribir el nombre exacto.

**Fuera de alcance**: `pg_dump`/`pg_restore` (el backup lógico en JSON es suficiente
a este tamaño; el backup de verdad del host sigue siendo del host), migrar esquema
durante el restore, restaurar `system` desde la UI.

**Tamaño**: M · `views/` de backups, middleware del gate, `urls.py`, plantilla,
tests, README (el modo mantenimiento y el aviso de las secuencias).

---

### S33 — Añadir un sello a una serie existente

**Depende de**: S15 (change set y commit por lotes), S16 (filas de `mode=new`),
S25 (borrar un sello, que es el mismo sitio de la barra).

**Lo que hay hoy**: `mode=new` crea la serie **con** sus filas; S17 clona una serie
entera; S25 borra un sello. En `mode=edit` la barra del grid no tiene ninguna
herramienta, y el change set del navegador envía siempre `op: "update"`
(`entryFor`). El backend, en cambio, **ya sabe**: `apply_changes()` acepta
`op: "create"` para un sello de una serie existente (`_insert_row`, con su test
`test_creates_a_stamp_of_an_existing_series`), escribe su fila de auditoría y
devuelve el id en `data.rows`. Lo que falta es la pantalla.

**Decisión**: la creación de un sello es una **fila borrador** dentro de la misma
rejilla, no un formulario aparte. Se añade con un botón `+ Stamp` en la barra de
`mode=edit`, entra en el change set con `op: "create"` y se escribe al commitear,
como cualquier otro cambio: la revisión la enseñanza antes de tocar la base y el
rechazo la devuelve con su mensaje.

- **Id temporal `new-<n>`**, el mismo prefijo que ya usa `mode=new`
  (`config.rowIdPrefix`); los ids reales son numéricos, así que no colisionan. Al
  commitear, la respuesta trae `id` y `updated_at`, y la fila pasa a ser real.
- **Qué se pide**: solo lo que el sello guarda. La serie ya está abierta y sus ocho
  atributos no se preguntan. `name` arranca con el de la serie (el mismo criterio
  que las filas de `mode=new`, que lo siguen hasta que se editan) y `face_value`
  vacío.
- **Una fila vacía no se envía**: si no se ha tocado nada, se descarta al
  commitear, como en `mode=new`. Tampoco puede quedar una fila a medias sin
  explicación: si falta un campo obligatorio, el servidor la rechaza y la fila se
  queda con el mensaje.
- **La revisión la lista como nueva**, sin `before → after`, y suma al contador
  de cambios. **`Ctrl+Z` la quita** (añadir es una entrada del historial) y
  borrarla antes de commitear no toca el servidor.
- **No se persiste en `localStorage`.** Un `create` no tiene `base`, así que el
  borrador solo guarda updates (igual que `mode=new`, que no guarda nada); el
  guard de `beforeunload` ya avisa cuando hay algo pendiente.
- **Tras un commit limpio, la página se queda en la serie** en vez de volver al
  workbench: el commit de hoy redirige con `?focus=<id>` porque el trabajo era
  editar una serie concreta, pero aquí el trabajo es añadir una fila **a esta**
  serie, y salir de ella es lo contrario de lo que se pidió.

**Aceptación**: se añade un sello, aparece como fila, la revisión lo lista como
nuevo, el commit lo escribe y la página no se va; la fila es entonces una fila
normal (editable, borrable con S25). La auditoría tiene su `create` y S21 lo
revierte como el resto (el sello desaparece). Una fila sin tocar se descarta sin
error. El contador de sellos de la barra cuadra. Recargar con una fila nueva
pendiente pregunta antes de salir. El change set sigue sin llevar M2M.

**Fuera de alcance**: los colores del sello nuevo (es el hueco conocido: el change
set no lleva M2M; se ponen desde la tabla de colores o al crear la serie), duplicar
filas o pegar TSV en `mode=edit` (eso es de `mode=new`), y añadir sellos desde el
workbench sin abrir la serie.

**Tamaño**: M · `issue_workspace.js` (op en el change set, fila borrador,
reconciliación de ids, revisión, historial), `templates/datadesk/issue_workspace.html`
(el botón), `views/workspace.py` (el prefijo de id en `mode=edit` y los textos),
`datadesk.css` (la fila borrador), tests de escritura (el `create` ya está) y de la
vista, y comprobación en navegador.

---

### S34 — El dinero, las fechas y el total del pie dicen lo que son

**Depende de**: S8 (workbench y endpoint del grid), S24 (la escala y el ancho de
las columnas), S28 (la piel y los `min` de columna).

**Lo que se vio en producción** (2.540 series, 9.555 sellos), por orden de
gravedad:

1. **El pie del workbench dice «Showing 1-100 of 2600 rows» y arriba pone
   «2540 issues».** El 2.600 no existe: Tabulator, en modo remoto, no sabe el
   total y lo deduce de páginas × tamaño (26 × 100). El endpoint **sí** devuelve
   `total` (y `page` y `last_page`), así que el número correcto ya viaja; lo que
   está mal es quién lo pinta.
2. **Las cantidades no llevan separador de miles y se recortan**: `37500.00 €` en
   el workbench, y en MNH de las dos rejillas `45000....`, `1875.0...`,
   `9000.0...`. Recortar un número es peor que recortar un nombre: el número **es**
   el dato. Y con `max_digits=8, decimal_places=2` hay que dejar sitio a
   `999.999,99 €`, que son doce caracteres, no los diez del comentario de
   `min: 104`.
3. **La fecha del workbench va en ISO** (`1850-01-01`) mientras el resto de la app
   habla el formato del idioma. Se lee como un código.
4. **La misma cifra se escribe de tres formas**: `2,540 series` en el panel,
   `5 / 2,540` en la navegación de la serie y `2540 issues` en el workbench.
5. **Dos palabras para la misma cosa**: *issues* en el menú y en el workbench,
   *series* en el panel, en el editor, en las tablas de referencia y en los
   mensajes de borrado.
6. **El paginador está en inglés también en castellano**: `First`, `Prev`, `Next`,
   `Last` los pinta Tabulator, no nuestros catálogos.

**Decisión**: el **servidor formatea y el script pinta**, que es la regla que ya
gobierna los títulos, los textos del pie y las URLs por fila. No hay `Intl` ni
plantillas de formato en JS.

- El endpoint del grid añade a cada fila los valores ya escritos de las columnas
  que se formatean (`date_text`, `mnh_text`, `used_text`), con el mismo mecanismo
  que ya añade `dependencies_url` y `delete_url` (`_with_urls` → una función
  `_with_display`). La columna lleva `"format": "money" | "date"` en su definición
  y un solo formateador genérico lee `row[field + "_text"]`, así que la décima
  columna que se formatee mañana no toca JavaScript.
- **Las cantidades llevan el separador de miles del idioma activo**, y la marca
  decimal con él: `37.500,00 €` en castellano y `37,500.00 €` en inglés. Nunca
  `37500.00 €`: sin agrupar, en una tabla de miles de filas, el número se cuenta a
  ojo y se cuenta mal. Se hace con `number_format(value, decimal_pos=2,
  force_grouping=True)`, que es lo que ya usa el panel, y el mismo criterio para
  los tres contadores (`2.540` / `2,540`).
- **Las fechas van en día/mes/año en castellano y en mes/día/año en inglés**, que
  es lo que pide cada idioma: una serie fechada el 1 de diciembre de 1853 se lee
  `01/12/1853` con la interfaz en castellano y `12/01/1853` con la interfaz en
  inglés. Es el `SHORT_DATE_FORMAT` del idioma activo (con ceros a la izquierda),
  nunca el ISO que se ve hoy. El formato sale del idioma de la petición, así que
  el conmutador EN/ES de la barra cambia fechas y cantidades a la vez.
- **El pie lo pinta el servidor**: la respuesta trae el texto de esa página
  (`Showing 1-100 of 2,540 rows` / `Mostrando 1-100 de 2.540 filas`), construido
  con `page`, `size`, `total` y el plural del catálogo, y sustituye al contador de
  Tabulator (`paginationCounter` con una función que devuelve esa cadena). Los
  cuatro botones: o se traducen con el módulo de idioma de Tabulator, o el pie es
  nuestro y nos llevamos también los botones; se decide al implementar, pero en
  castellano no puede quedar `Next`.
- **El contador de arriba usa el mismo número ya escrito** (`total_text`), para
  que el panel, la navegación y el workbench no puedan discrepar.
- **Una sola palabra**: *series* en la interfaz (el panel ya la usa; el menú y el
  workbench son los que se desvían). Solo texto: ni URLs (`/datadesk/issues/`),
  ni nombres de plantilla, ni el modelo `Issue`.
- **Anchos**: los `min` de MNH y Used suben a lo que mide `999.999,99 €` (120 px)
  en las dos rejillas, y la columna del sello (`width: 90`) pasa a ese mínimo. La
  fecha mantiene su ancho fijo de 112.

**Aceptación**: el pie y el contador dicen el total real (2.540, no 2.600) y las
dos cifras coinciden; las cantidades llevan el separador de miles del idioma
(`37.500,00 €` / `37,500.00 €`) y **no se recortan** con el valor máximo posible;
las fechas se leen `01/12/1853` en castellano y `12/01/1853` en inglés, nunca en
ISO; los tres contadores usan el mismo formato; en castellano no queda ninguna
palabra inglesa en el paginador; el orden de las columnas sigue siendo por el
valor crudo, no por el texto pintado. Tests: que el texto del pie sale de `total`
y no de páginas × tamaño; que `999.999,99 €` cabe en el `min` de las columnas de
dinero; y uno con una serie fechada el 1 de diciembre de 1853 que fija los dos
textos, `01/12/1853` y `12/01/1853`, para que nadie «unifique» el formato.

**Fuera de alcance**: la prosa de la tira (los `textarea` de descripción y nota
cortan a dos filas; si se quiere, entra aquí como detalle menor, pero es otro
asunto), el ancho de los `select` de la barra de filtros, y cualquier cambio de
datos.

**Tamaño**: S–M · `views/workbench_api.py` (`_with_display`, el pie),
`views/workbench.py` (los `min` y el contador), `views/workspace.py` (los `min`
del sello), `service.py` (los valores que se formatean), `workbench.js` y
`issue_workspace.js` (el formateador genérico y el contador), `base.html` y
`workbench.html` (*series*), los dos catálogos `.po`/`.mo`, tests y comprobación
en navegador con la serie de 1853.

---

### S35 — Cambiar los colores de un sello desde el panel de la imagen

**Depende de**: S18 (el patrón de campo escrito con autocompletado y `+ Crear`),
S19 (la tabla de colores, renombrar y fusionar), S29 (el panel de la imagen) y S33
(las filas borrador, que también llevan colores).

**Lo que hay hoy**: `Stamp.colors` es una M2M y el change set no la llevaba, así
que en `mode=edit` la celda solo pinta chips; elegir un color solo se puede al
crear una serie (`mode=new`, con el editor `list` de Tabulator) o desde las tablas
de referencia, que renombran y fusionan pero no asignan. Es el hueco que quedó
anotado al cerrar S22.

**Lo que ya está hecho, y es casi todo**: `/apply` acepta `colors` en un `update`
(`_colors_of()` los saca del patch antes del serializer y `_update_row()` hace
`obj.colors.set()`), `snapshot()` guarda la M2M como ids ordenados, y el revert de
S21 **también los devuelve** (`_restore()` los saca del `before` y hace `set()`).
Hay creación de colores (`lookups/color/create`) y la paleta con su tono
(`colour_options()`).

**Decisión**: el editor vive en **el panel de la imagen de S29**, no en la celda.
Los colores son parte de lo que se ve en la pieza —como el dentado— y el panel ya
es donde se mira el sello; la celda sigue siendo de lectura (un `list` de Tabulator
en una fila de 38 px no cabe, y en `mode=new` ya está el editor de la fila rápida).

- **Chips con × y un campo con autocompletado**, el patrón de S18: un `input list`
  con el `datalist` de colores y un `+ Crear "X"` que aparece cuando el nombre
  escrito no existe, más un chip por color con su tono y su × para quitarlo. Nada
  cuelga de la foto: ni hover ni clic sobre la imagen (la regla de S29 se mantiene).
- **Un solo idioma para el color: el id.** `serialize_stamp()` manda
  `colors: [id, id]` en vez de `{name, tone}`, y el nombre y el tono salen de la
  paleta que viaja en la página. Así el valor de la fila, el patch, la revisión, el
  borrador y el `localStorage` hablan de lo mismo, y `patch.colors` es una lista de
  ids sin traducción por el medio.
- **La paleta viaja también en `mode=edit`** (`config.colours`, que hoy solo se
  manda en `mode=new`). Es una excepción consciente a la regla de S18 —allí se
  dejaron de mandar artistas e imprentas— y tiene motivo: un editor de varios
  valores necesita sus opciones de antemano, y resolver un nombre escrito a su id
  exige la tabla entera. Con los datos reales son **300 colores**, no las «decenas»
  que suponía este plan: unos 18 KB de JSON en cada página de serie (nginx lo
  comprime a una cuarta parte). Para un usuario en una LAN es aceptable; si molesta,
  la salida es un endpoint `lookups/color/all` con ETag que se pida al abrir el
  editor.
- **La columna lleva `patch: "colors"` solo en `mode=edit`**, con lo que el color
  entra en el change set sin maquinaria nueva: `entryFor`, `sync`, revisión,
  `Ctrl+Z`, `beforeunload` y el borrador ya saben qué hacer con un campo más.
  Consecuencia buena: **un borrador de S33 también puede llevar colores** antes de
  commitear (el `create` ya acepta `colors`), que era su «fuera de alcance».
- **El control es el mismo en los dos modos**: en `edit` escribe la celda y hace
  `sync` + `push`; en `new` escribe la celda y actualiza el borrador de la fila
  (el mismo gancho que ya usa la descripción en el panel). En `mode=new` conviven
  con el editor de la fila rápida y no se pelean: los dos escriben el mismo valor
  de la fila.
- **Los nombres para la revisión y el deshacer** salen del mapa de lookups, que se
  siembra con la paleta al arrancar (`rememberLookup("color", id, nombre)`): así el
  panel escribe `Rosa · Violeta → Azul`, y un borrador restaurado de `localStorage`
  sigue mostrando nombres y no ids.
- **Comparar como conjunto**: `same()` compara `String(valor)`, así que `[1,2]` y
  `[2,1]` parecerían un cambio; se normaliza la lista de colores antes de comparar.
- **La celda vacía pinta `—`**: `colorsFormatter` devuelve `""` cuando el sello no
  tiene colores, y hay 1.648 sellos así en producción, o sea que el hueco se ve.
- **El panel `New colour` de la barra se queda**: lo decidió el usuario al abrir
  el paso. El `+ Crear` del panel hace lo mismo con el nombre ya escrito, pero el
  botón crea un color sin tener que seleccionar un sello, así que las dos puertas
  conviven y comparten la paleta (`addToPalette`).

**Aceptación**: se selecciona un sello, se le añade un color desde el panel y la
revisión lo lista como un cambio más (`Colors: Rosa · Violeta → Azul`); quitar un
chip también; el commit los escribe y la recarga los enseña; `Ctrl+Z` deshace
añadir y quitar; un color desconocido se crea con `+ Crear "X"` y queda asignado
en el mismo gesto; un sello sin colores enseña `—` en la celda y «ninguno» en el
panel sin romper nada; un borrador de S33 admite colores antes de commitear. La
auditoría guarda los ids en `before` y `after`, y el revert de ese commit devuelve
los colores anteriores.

**Tests que hoy no existen**: un `update` de colores por `/apply` (hoy solo está
probado el `create` de una serie con colores), dejarlos en `[]` para quitarlos
todos, el revert de un cambio de color (la rama `_restore` de S21 está sin cubrir
para M2M) y el `config` de la página (la paleta en `mode=edit`, `patch` en la
columna y los ids en la fila).

**Fuera de alcance**: renombrar y fusionar colores (S19), crear un color que no sea
desde el campo del panel (el `+ Crear` lo cubre), el orden de los chips (van por
nombre, como en la celda) y el filtro por color del workbench (S30 ya lo tiene).

**Tamaño**: M · `service.py` (ids en la fila), `views/workspace.py` (la paleta y el
`patch` de la columna), `issue_workspace.js` (el control del panel, los ganchos de
los dos modos, `same`, la revisión y la siembra de nombres), la plantilla del panel,
`datadesk.css` (los chips del panel), tests de escritura y de revert, y
comprobación en navegador con la serie de 1853.

---

### S36 — El orden de la lista lo decide el código de la serie

**Depende de**: S7 (el queryset de lectura), S8 (el grid y su paginación), S9 (la
medida del coste).

**Lo que pasaba**: el orden por defecto era año → fecha → **nombre**, y ahí se
acababa. Dos series de la misma fecha con el mismo nombre —que es el caso normal:
una emisión parte en varias series del mismo día— quedaban empatadas y el orden lo
decidía la base: distinto entre peticiones, y con `OFFSET` capaz de repetir una
fila en dos páginas y saltarse otra. En los datos reales hay 419 fechas repetidas.

**Decisión**: el desempate es el **código de la serie en el catálogo**, y el orden
es **total** (la última clave es el `pk`).

- **Qué código**: el del primer sello, tomando **Fesofi** y cayendo a **Edifil** por
  sello. Al revés no vale: 2.761 de 9.557 sellos no tienen Edifil (696 series sin
  ninguno), y solo 61 no tienen Fesofi. Un `""` cuenta como «sin código», porque la
  columna es nullable pero el grid también escribe vacío.
- **Cómo se compara**: por **longitud y luego texto**, que es el orden numérico para
  los códigos de la misma familia y deja los especiales detrás: «3649» antes que
  «1998042». Las series sin ningún código van al final de su fecha.
- **Dónde**: en `chronological_order()`, que usan el grid, `issue_positions()` (las
  flechas de la serie y el `1.234 / 2.540`) y `page_of_issue()`. Cualquier otra
  columna ordena por lo que se pidió y **termina en el mismo desempate**, así que
  dos clics en «Name» tampoco pueden desordenar la lista.
- **Qué cuesta**: una anotación `Min` sobre la unión que ya se hacía para contar
  sellos. Medido con los datos reales: página del grid 65 → 68 ms, contadores del
  panel 21 → 20 ms, posiciones de la serie 2 → 8 ms. Sin índice nuevo.

**Aceptación**: dos series del 1-1-1853 salen por su código (Isabel II 0017 antes
que Escudo de Madrid 0022) y no por su nombre; las quince del 29-12-1998 salen por
código y la del código especial al final; una serie sin códigos va la última de su
fecha; paginar de una en una devuelve cada fila una sola vez. Siete tests en
`test_service_read.py`, y la suite corre en SQLite mientras los números se
comprobaron en Postgres, así que el `NULLS LAST` y el `LENGTH` están fijados en los
dos motores.

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

Cada paso ha llegado a `development` por su propia rama y PR; las entradas de esta
bitácora cuentan lo que se hizo, no lo que falta — lo que falta está en §3 con su
`⏳`. El plan y el diseño viven dentro del repo (`memory-bank/`), no en
`~/.opencode`, para que un rebuild del contenedor no los borre.

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

### ✅ S15 — Panel de revisión y commit por lotes (2026-11-19)

Ficheros modificados:

```
backend/datadesk/views/workspace.py            field_labels(), BACKUP_THRESHOLD, backupUrl/backupThreshold,
                                               fieldLabels/modelLabels, texts de copia, plural "commit"
backend/datadesk/views/workbench.py            focus → page_of_issue(); grid_config(initial_page, focus)
backend/datadesk/service.py                    page_of_issue(): posición de la fila con la orden por defecto
backend/datadesk/views/write_api.py            BackupJsonView (POST /datadesk/backup)
backend/datadesk/urls.py                       backup
backend/datadesk/templates/datadesk/issue_workspace.html  panel lateral; el pie deja Review changes
backend/datadesk/static/datadesk/issue_workspace.js       renderReview(), commit con redirect y errores por
                                               entrada, backup, Ctrl+Enter, Esc cierra el panel
backend/datadesk/static/datadesk/workbench.js  página inicial y fila enfocada
backend/datadesk/static/datadesk/datadesk.css  dd-review-*, dd-row-focus
backend/datadesk/locale/{en,es}/…              textos del panel y plural "commit"
backend/datadesk/tests/test_workspace_edit.py  +4 (labels, modelos, backup, panel)
backend/datadesk/tests/test_workbench_api.py   +4 (focus y página)
backend/datadesk/tests/test_write_api.py       +6 (endpoint de copia)
```

Decisiones tomadas al implementar:

- **El panel es un cajón lateral oculto por defecto** (`Review changes` en el
  pie), no una vista siempre visible: la franja y el grid tienen que seguir
  legibles mientras se compara el cambio con la fila que lo originó. Commit y
  Discard viven dentro; el pie conserva Undo/Redo y el contador.
- **`Ctrl+Enter` confirma** y `Shift+Enter` sigue haciéndolo: el atajo viejo no
  se quita porque ya estaba en los dedos, y el nuevo es el que el plan pide. El
  handler de `Shift+Enter` ignora `Ctrl` para que `Ctrl+Shift+Enter` no confirme
  dos veces.
- **Commit limpio → workbench con la serie enfocada**: el grid pagina en
  servidor, así que el número de página se resuelve en `page_of_issue()` —sobre
  una lista de pks, no sobre el join de ocho tablas— y el JS selecciona y
  desplaza la fila una sola vez. Llega sin filtros: el foco es una ayuda de
  aterrizaje, no un filtro que se herede del workspace.
- **Rechazo parcial**: las filas aplicadas salen del buffer, las rechazadas se
  quedan **con su mensaje** en el panel (`entry.error`, que se borra en la
  siguiente edición de esa fila) y el panel se abre solo. No se pierde nada
  tecleado.
- **`refusal()` recibía el objeto de errores en vez del cuerpo** y devolvía
  siempre el texto genérico: lo cazó el arnés de jsdom, no los tests de Python.
  Corregido usando `firstError(errors)` donde hay errores y `refusal(body, …)`
  donde hay cuerpo.
- **Copia de seguridad a mano, nunca automática**: `POST /datadesk/backup`
  ejecuta el comando que ya existía (`stamps_db_backup`, modo `stamps`) con un
  nombre generado, y devuelve la ruta relativa. El botón aparece a partir de 20
  cambios (`BACKUP_THRESHOLD`); por debajo, escribir un fichero es ruido. Un
  fallo de la copia se cuenta en el panel y **no** impide confirmar: bloquear el
  commit por un disco lleno no arregla nada.
- **El volcado es síncrono**: son 12.700 objetos y un único usuario; un trabajo
  en segundo plano con su estado era más máquina que problema.

Verificado: `pytest datadesk` → **269 en verde**; suite completa **1285 en
verde** · catálogos recompilados · arnés de jsdom ampliado a **42
comprobaciones** (panel, etiquetas, antes→después, Esc, `Ctrl+Enter`, rechazo con
mensaje, umbral de copia) · `page_of_issue()` testeado con más de una página y
con filtros.

### ✅ S16 — `mode=new` completo (2026-11-19)

Ficheros modificados:

```
backend/datadesk/views/workspace.py            REPEAT_FIELDS, FAST_FIELDS, repeat_values(),
                                               IssueNewView (?from=), colour_options(),
                                               config de `new`: ids, fastRow, colours, createUrl,
                                               newUrl, fieldLabels, texts
backend/datadesk/templates/datadesk/issue_workspace.html  Fill series, Fast row, Create series,
                                               barra `created-bar`; se va el aviso «no guarda»
backend/datadesk/static/datadesk/issue_workspace.js       create, refuse, showCreated, fillSeries,
                                               nextCode/bumpLetters, duplicate (Ctrl+D), paste TSV,
                                               fast row, editor de colores, Shift+Enter
backend/datadesk/static/datadesk/datadesk.css  dd-grid-tools, dd-fast, dd-created(-page)
backend/datadesk/locale/{en,es}/…              textos nuevos, dos avisos retirados
backend/datadesk/tests/test_workspace_new.py   14 pruebas nuevas (configuración, payload y bucle)
```

Decisiones tomadas al implementar:

- **El bucle es una página del servidor, no un borrador**: tras crear, la barra
  ofrece `Create another in <year>`, que abre `/datadesk/issues/new/?from=<pk>` y
  el servidor rellena el formulario desde esa serie. Así `mode=new` sigue sin
  escribir nada en `localStorage` (regla de S11) y el bucle se puede probar con
  Django, sin navegador.
- **`REPEAT_FIELDS` no contradice a `PREFILL_FIELDS`, y la diferencia es la
  fuente**: el prefill copia país y año de la *última* serie, que puede ser de
  hace meses; el bucle copia además la clasificación y la perforación de una
  serie guardada hace segundos, que casi seguro es de la misma emisión. Lo que
  identifica a una serie (`name`, `date`) y lo que es del conjunto
  (`total_printed`, valores de mercado, textos) se limpia en los dos casos.
- **Tras crear, el workspace deja de editarse**: el formulario y el grid se
  ocultan y quedan las dos acciones que tienen sentido (abrir la serie o crear
  otra). Dejar los campos vivos habría prometido un guardado que ya no existe.
- **`?from=` no redefine el botón `↺ Use last issue`**: el botón sigue
  significando «la última serie» y lleva sus propios valores; el bucle solo
  rellena el formulario. Coinciden en la práctica porque la última serie suele
  ser la que se acaba de crear, pero la etiqueta no miente.
- **Filas vacías no son sellos**: se descartan las que nadie ha tocado y no
  tienen ni código ni valor facial ni colores, para que `rows=4` no obligue a
  teclear cuatro sellos. Una fila tocada y vaciada sí se envía y el servidor la
  rechaza con su mensaje, que es más honesto que borrarla por su cuenta.
- **`Fill series` avanza lo que varía**: con sufijo alfabético mueve la letra
  (`2744a → 2744b`, `z → aa`) y conserva el número; sin sufijo incrementa el
  número conservando los ceros (`0069 → 0070`). Un primer código sin dígitos no
  inventa secuencia: avisa y no escribe nada. Cada celda pasa por `cellEdited`,
  así que `Ctrl+Z` deshace el relleno igual que si se hubiera tecleado.
- **`Ctrl+D` inserta debajo de la fila del cursor**, no al final: numerar es
  copiar y seguir. La copia nace marcada como tocada, para que el nombre de la
  serie ya no la reescriba.
- **El pegado TSV se alinea con lo que se ve**: columnas visibles (con fila
  rápida activa son cuatro), desde la celda del cursor hacia abajo y a la
  derecha. Un pegado de una sola celda no se intercepta: es el pegado normal del
  editor.
- **Editor de colores solo en `mode=new`**: la aceptación de S16 pide colores al
  crear, y en `mode=edit` las filas llevan `{name, tone}` sin id y el change set
  no transporta M2M. Se usa el editor `list` con `multiselect` y los ids viajan
  al servidor; la búsqueda y la creación al vuelo llegarán con S18. Ojo:
  `autocomplete` **desactiva** `multiselect` en Tabulator 6, así que no se usa.
- **Mensajes de rechazo por campo**: los errores de la franja se muestran como
  `Etiqueta: mensaje` con las etiquetas del servidor (`fieldLabels`), y los del
  sello como `Sello N: mensaje`, marcando la fila en rojo. Los textos de DRF
  siguen en inglés hasta que una pantalla los traduzca (decisión de S12).

Revisión tras el primer uso real (2026-11-19):

- **Quitar una fila**: el grid de `mode=new` gana una columna `×` (34 px, oculta
  nunca: se borra mientras se teclea). El borrado **es un paso de deshacer**: se
  guarda la fila y su posición en el historial, así que `Ctrl+Z` la devuelve
  donde estaba y `Ctrl+Shift+Z` la vuelve a quitar. Sin eso, un clic en la
  columna equivocada se llevaba una fila con colores y no había forma de
  recuperarla.
- **Los colores se cortaban**: la celda recorta lo que no cabe y el navegador
  contestaba con `...`, que no dice nada. Ahora pinta **un** chip y `+N` con el
  resto, y la lista completa viaja en el `title`; el editor sigue enseñándolos
  todos. Es deliberadamente un chip y no dos: un nombre largo más `+N` cabe
  siempre, y adivinar cuántos caben según el ancho volvería a cortar.
- **`Fill series` numera Edifil y Fesofi**: las dos catalogan el mismo conjunto
  con secuencias distintas, así que el botón avanza **cada columna que tenga
  primer código** y se salta en silencio la que esté vacía (lo normal es tener
  una sola). Las columnas se planifican **antes** de escribir ninguna: si la
  segunda no se puede numerar, la primera no queda a medias y el mensaje nombra
  la columna (`The first Fesofi code has no number to continue from.`). Las
  columnas y sus etiquetas vienen del servidor (`fillColumns`), no del script.
- **La fecha decide el año (2026-11-19, tras el primer uso)**: la pantalla de
  `mode=new` abre con **la fecha de hoy** cuando la serie que se va a teclear es
  del año en curso (o cuando no hay año que copiar, base vacía), y el campo año
  sigue a la fecha y queda **de solo lectura** mientras haya fecha: una serie se
  fecha una vez, no dos, y «1987» con fecha de 2026 no es una serie que nadie
  quisiera guardar. Vaciar la fecha devuelve el año a mano, que es como se
  registra una serie de la que solo se conoce el año: el año sigue siendo el
  único obligatorio de los dos. Para una serie de otro año la fecha nace **vacía**
  a propósito — inventar un día de 1987 es peor que dejarlo en blanco, y es la
  herencia contra la que avisaba el plan—; el prefill y el bucle siguen mandando
  el año y la fecha se teclea si se conoce. La fecha lleva los mismos límites
  (1800-01-01 a año+2-12-31) que el año, para que el navegador frene la errata
  antes de que llegue al servidor. Efecto lateral aceptado: `↺ Use last issue`
  ya solo cambia el país cuando hay fecha, porque el año no es suyo.
- **El error se marca en el campo, no en la pantalla**: `markFields()` pone
  `dd-input-invalid` en los controles que el servidor nombró (el mensaje ya era
  `Etiqueta: mensaje`, pero no decía dónde), lleva el foco al primero y lo
  desplaza a la vista; el anillo del formulario entero (`dd-meta-error`) queda
  solo como recurso cuando el error no nombra ningún campo. En el grid,
  `markCells()`/`markStampCells()` ponen `dd-cell-invalid` en la celda concreta
  —la fila en rojo es el contexto, la celda es el campo— y si esa columna está
  oculta por la fila rápida, la fila rápida **se apaga** para que el anillo tenga
  dónde verse. Toda marca desaparece al editar ese campo o al reintentar.

Verificado: `pytest datadesk` → **290 en verde**; suite completa **1306 en
verde** · catálogos recompilados · arnés de jsdom de `mode=new` con **57
comprobaciones** (filas, fila rápida, numeración de las dos columnas con sufijo,
con ceros y con una bloqueada, código no numérico, `Ctrl+D`, quitar fila y
`Ctrl+Z`, pegado TSV, payload con nombres de modelo, colores como ids, barra de
creado, rechazo por sello y por campo con su anillo, columna oculta revelada,
fecha por defecto, año derivado y liberado al vaciar la fecha, y `Shift+Enter`)
y las **42** de `mode=edit` siguen pasando.

### S17 — Clonar y borrar (2026-11-19)

`datadesk/dependencies.py` (nuevo) y tres endpoints nuevos, más los dos botones
en la franja de la serie:

- **`dependencies.py`**: `Dependencies` (sellos, ítems, colecciones),
  `series_dependencies()` — dos consultas: los sellos de la serie y un agregado
  sobre la tabla intermedia con `Count("collection_id", distinct=True)`, porque
  la misma colección suele tener varios sellos de la serie — y
  `dependency_warning()`.
- **`clone_series()`** en `write.py`: copia con `_copy_fields()`, que lee
  `attname` de `_meta.concrete_fields` (así `year_id`, `country_id`… viajan sin
  resolver lookups otra vez) y se salta la PK y `updated_at`. Los sellos se
  copian igual, con un `colors.set()` desde el origen. Una transacción, una fila
  de auditoría por objeto escrito.
- **`delete_series()`** en `write.py`: `select_for_update()` sobre la serie
  (sin `select_related`: un `FOR UPDATE` sobre los LEFT JOIN de país/artista es
  un error en PostgreSQL), comprobación del año, recuento **dentro** de la
  transacción, una fila `delete` por sello y otra por la serie con el `before`
  completo, y `issue.delete()` (la cascada se lleva sellos e `CollectionItem`).
- **`write_api.py`**: `IssueCloneJsonView` (devuelve `data.url`), 
  `IssueDependenciesJsonView` (GET, staff, 404 si no existe) e
  `IssueDeleteJsonView` (400 con `errors.confirm` si el año no coincide).

Decisiones tomadas al implementar:

- **Clonar no revalida**: el clon copia filas reales, no un formulario, así que
  `create_series()` no se reutiliza aquí. Pasar la copia por los serializers
  habría convertido «clonar» en «volver a teclear» y habría rechazado series
  con huecos (un `face_value` vacío es NOT NULL y el serializer lo rechaza), que
  son precisamente las que se clonan para arreglarlas.
- **El nombre y los códigos se copian tal cual**: renombrar es del usuario y la
  copia se abre en el workspace para que lo haga. Nada de «(copia)»: sería una
  cadena que nadie eligió, dentro del catálogo.
- **`year`/`date` se pueden sobreescribir por la API** aunque la interfaz no lo
  pida todavía: clonar al año siguiente es el motivo normal, y hacerlo en la
  franja después es una edición más del change set. `date: null` limpia la fecha
  y la ausencia de la clave la copia; de ahí que la vista filtre claves en vez
  de leer con `get()`.
- **La procedencia va en el `after` del clon**: `cloned_from` es procedencia, no
  un campo. Solo aparece en filas `create` y el revert de S21 borra lo que creó
  un `create` en vez de reconstruirlo desde el `after`, así que el snapshot
  sigue siendo «splatteable». Los sellos no llevan la marca: vinieron de la
  serie, no de otra serie.
- **El preview es un GET aparte y el borrado recuenta**: el diálogo se abre con
  números frescos y el endpoint de borrado vuelve a contar dentro de su
  transacción. Un `CollectionItem` añadido entre abrir y pulsar no puede quedar
  fuera del recuento.
- **La frase no lleva números**: `dependency_warning()` devuelve una de tres
  frases (sin sellos / nadie los tiene / están en colecciones) y los tres
  números van en su propia lista del diálogo. Así no hay plurales anidados que
  resolver en dos idiomas.
- **Confirmar es teclear el año, y lo comprueba el servidor**: el diálogo no
  desactiva el botón cuando el texto no coincide — un botón muerto sin
  explicación es peor que un mensaje. El 400 nombra el año que hay que teclear.
- **`Clone`/`Delete` se desactivan con cambios pendientes** (y el `title` dice
  por qué): la copia se hace de la base y el borrado ignora la pantalla, así que
  ninguna de las dos puede convivir con un buffer sin confirmar.
- **El borrado no entra en el change set ni en `Ctrl+Z`**: es un diálogo con su
  propia confirmación, como decidió S14. Después de borrar, la página vuelve al
  workbench; después de clonar, salta a la copia (el workspace que había era el
  origen).

Verificado: `pytest datadesk` → **328 en verde**; suite completa **1344 en
verde** · catálogos recompilados (`Clone`, `Delete`, `Collection items`,
`User collections`, la caja del año y los textos del script) · arnés de jsdom de
`mode=edit` con **62 comprobaciones** (las 42 anteriores más: botones
desactivados con buffer, preview con sus tres números y su frase, etiqueta con
el año, año equivocado que no navega, año correcto que vuelve al workbench,
`Esc` que cierra el diálogo sin salir, y el clon que salta a la copia) y las 57
de `mode=new` siguen pasando. El arnés tuvo que sustituir
`window.location.assign` al evaluar el script (`location` no se puede redefinir
en jsdom) y `HTMLElement.prototype.scrollIntoView`, que jsdom no implementa.

### S18 — Crear un lookup desde el workspace (2026-11-19)

`search_lookups()` en `service.py`, `LookupSearchJsonView` y los campos de
referencia convertidos en campos tecleados:

- **`service.search_lookups(key, query, limit=50)`**: `icontains` sobre la
  columna que identifica la fila, ordenada por ella, cortada en 50. Una consulta,
  y la misma para los ocho lookups del registro.
- **`LookupSearchJsonView`**: GET, staff, 404 para una clave desconocida.
  `LookupCreateJsonView` (S12) añade `tone` cuando la clave es `color`, porque
  el chip de la celda se pinta con el tono y un color recién creado no tiene
  fila en la configuración de la página de la que copiarlo.
- **`workspace.py`**: `lookup_label()` sustituye a `lookup_options()` (la franja
  manda el nombre de la fila elegida, no la tabla entera) y la configuración
  gana `lookups` (search + create por clave), `lookupLabels` y `lookupText`. El
  prefill viaja como `{"value", "label"}` para que el botón pueda rellenar la
  caja igual que lo haría una persona.
- **Plantilla**: `<input list="lookup-<field>">` + `<datalist>` + el botón
  `+ Crear "X"`, oculto hasta que el texto no es una fila conocida.
- **`issue_workspace.js`**: dos mapas (`id→nombre`, `nombre→id`) como diccionario
  entre lo que la API habla y lo que se teclea, sembrados desde el DOM y
  ampliados por cada búsqueda y cada fila creada; búsqueda con 250 ms de
  retardo; `formValue()` traduce en un solo sitio y lo usan los dos modos.

Decisiones tomadas al implementar:

- **El campo es un `<input list>`, no un combobox propio**: el navegador filtra,
  navega con el teclado y anuncia el campo a un lector de pantalla sin una línea
  de código, y el `datalist` se rellena desde la búsqueda. Un menú propio habría
  costado más código que el que ahorra.
- **El formulario sigue hablando ids**: la franja envía ids como la API, la caja
  muestra nombres, y la traducción ocurre en `formValue()`/`setLookup()`. Por eso
  `seriesPayload()`, `formValues()`, `readValue()`, `writeValue()` y el log de
  deshacer pasan por ahí: el historial guarda **ids** (como el patch) y al
  deshacer se escribe el nombre que el mapa recuerde, de modo que `Ctrl+Z` no
  deja la caja con un número dentro.
- **Un nombre sin fila no se envía**: `unresolvedLookup()` lo detecta antes de
  crear o confirmar, marca el campo con `dd-input-invalid` y explica que hay que
  usar el botón `+`. Sin ese control, `""` en una FK nullable habría borrado el
  valor en silencio: el `_prepare_patch` de S12 convierte `""` en `NULL` a
  propósito.
- **La fila se crea al pulsar, no al confirmar**: sin ids temporales (decisión de
  S12), la fila existe en cuanto se crea y el endpoint la audita. Por eso en
  `mode=edit` **no entra en el buffer**: el panel de revisión la enseña en un
  grupo aparte («New reference rows · ya guardada»), y el botón `Review changes`
  se habilita también cuando solo hay filas de esas. `Discard` no la borra: es
  una fila de referencia reutilizable, igual que el `Year` implícito de S12.
- **Los colores se crean desde la barra del grid**, no desde la celda: el editor
  es la lista multiselección de Tabulator, que no acepta texto libre. El botón
  `New colour` abre un diálogo, crea la fila y la añade a la lista que la celda
  ofrecerá la próxima vez; elegirla sigue siendo editar la celda.
- **El borrador guarda también el diccionario**: un cambio de artista restaurado
  desde `localStorage` en una página que nunca lo buscó habría enseñado un id y
  habría deshecho a una caja vacía, así que el draft lleva `lookups: [[campo:id,
  nombre]]` y se siembra al recuperar.
- **En `mode=edit` los colores siguen de solo lectura**: el change set no lleva
  M2M. No entraba en la aceptación de este paso y la pantalla de lookups de S19
  es su sitio natural.

Verificado: `pytest datadesk` → **349 en verde**; suite completa **1365 en
verde** · catálogos recompilados (`+ Create`, `New colour`, `Added to the list.`,
`New reference rows` y el aviso de nombre sin fila) · arnés de jsdom de
`mode=new` con **73** comprobaciones (las 57 anteriores más: el país prefillado
enseña el nombre y guarda el id, botón `+` que aparece con un nombre nuevo y
lleva el nombre, búsqueda al servidor tras 250 ms, `datalist` relleno, nombre
buscado que ya no se ofrece para crear, creación que deja el nombre en la caja y
envía el **id** al crear la serie, y diálogo de color que añade el color a la
lista que la celda ofrecerá) y `mode=edit` con **74** (nombre y id sembrados,
mismo nombre no es cambio, nombre desconocido que **para** el commit con su
aviso y su anillo, `+` que crea y envía el id en el change set, y el panel de
revisión con `Artist · Pepito` y su «ya guardada»).

### S19 — Pantalla de lookups y fusión (2026-11-19)

`datadesk/lookups.py` (servicio), `datadesk/views/lookups.py` (pantalla y
endpoints), dos plantillas y el JS de la pantalla:

- **`datadesk/lookups.py`**: `usage_counts()` (un `Count` por relación, accesor
  sacado del campo, `distinct=True`), `lookup_page()` (dos consultas, página
  clavada), `rename_lookup()`, `delete_lookup()`, `merge_lookups()` y
  `create_next_years()`.
- **`views/lookups.py`**: índice con las ocho tablas y su tamaño, la tabla con
  pestañas, `rows` (paginado al estilo Tabulator), `rename`, `delete`, `merge` y
  `years/next`. `lookup_config()` manda URLs, columnas y **todos** los textos.
- **`lookups.js`**: grid remoto, edición inline del nombre, fusión de las dos
  filas seleccionadas, borrado con su motivo cuando está en uso.

Decisiones tomadas al implementar:

- **Dos consultas por página, no una**: el plan decía «una query», y son dos —el
  `count` que necesita la paginación y la página en sí—. Lo que el plan quería
  evitar era el `count()` por fila, y eso está garantizado: el test lo fija en
  dos con `CaptureQueriesContext`.
- **El accesor inverso se deduce del campo**, no de una segunda tabla de nombres:
  `Issue.artist` ya sabe que es `issues`. Añadir un lookup nuevo al registro no
  obliga a tocar nada más.
- **Un nombre repetido es una oferta, no un error**: el 409 lleva
  `existing_id`/`existing_name` y la pantalla abre el diálogo de fusión con la
  fila editada como origen y la que ya tenía el nombre como superviviente — que
  es literalmente lo que el usuario estaba pidiendo al escribir ese nombre.
- **`keep_name_from` conserva las letras del plan**: `a` es el nombre de la fila
  que sobrevive y `b` el de la que desaparece. La interfaz lo traduce a dos radios
  sobre los nombres, no a letras.
- **El orden del `keep_name_from="b"` es el del plan y no es negociable**: mover →
  borrar el origen → renombrar. El renombrado va en su propio savepoint para que
  un `IntegrityError` se convierta en 409 y la transacción entera se caiga.
- **`updated_at` a mano también en los sellos** cuyos colores cambian: el plan lo
  pedía para las FKs y la misma razón vale para la M2M — el chequeo de conflicto
  de S12 compara esa columna.
- **El botón de borrar no se pinta cuando hay uso**: se pinta el motivo («En uso:
  fusiónala con otra fila»). Un botón desactivado sin explicación es lo que hizo
  que el `↺ Use last issue` pareciera muerto en S11.
- **La pantalla no crea filas**: crear vive donde se necesita (el workspace de
  S18) y los años tienen su acción propia. Añadir un «nueva fila» aquí sería un
  segundo sitio que hace lo mismo con otro nombre.
- **El sobre JSON y los plurales se compartieron**: `views/envelope.py`
  (`JsonPostView`, `written()`, `failure()`, `read_json()`) lo usan ahora el
  workspace y las lookups, y `texts.plural_forms()` sustituye al helper privado
  de `workspace.py`. Dos copias del mismo sobre acababan divergiendo.
- **El dashboard enlaza la pantalla**: sin enlace, las lookups solo se alcanzaban
  escribiendo la URL. S20 hará el dashboard de verdad y la pondrá en su sitio.

Verificado: `pytest datadesk` → **389 en verde**; suite completa **1405 en
verde** · catálogos recompilados (las etiquetas de la pantalla, los avisos de uso
y los cuatro plurales) · `lookups.js` no contiene una sola cadena visible: los
textos y los plurales llegan en la configuración · un test comprueba que **todos
los `getElementById` del script existen en la página**, porque un id renombrado
deja la pantalla rota en silencio · **40 tests nuevos** (6 del grid —recuentos,
búsqueda, dos consultas por página—, 6 de renombrar, 2 de borrar, 11 de fusión
—FK, M2M con un sello que tiene los dos colores, años con `CASCADE`, el orden de
`keep_name_from="b"` y la fila única de auditoría—, 2 de los años y 13 de
contrato HTTP).

### S20 — Dashboard y colas «needs attention» (2026-11-19)

`service.QUEUES` + `dashboard_queues()`, `views/dashboard.py` y la plantilla del
dashboard:

- **`service.QUEUES`**: el emparejamiento contador ↔ filtro ↔ etiqueta ↔ unidad,
  una vez. `ATTENTION_CONDITIONS` pierde `stamps_without_image` y gana un
  comentario que explica por qué esa cola no es una condición de queryset.
- **`picture_gaps()`**: un recorrido del índice que devuelve el número de sellos
  sin imagen **y** las series que los tienen, para que el contador y el filtro no
  puedan contar cosas distintas. `missing_data_report()` y `filter_issues()` lo
  comparten.
- **`dashboard_queues()`** usa `filter_issues()` para el segundo número de las
  tarjetas de sellos, así que la tarjeta y el total de la rejilla son la misma
  consulta.
- **`views/dashboard.py`**: formatea los números con `number_format` (idioma),
  separa «necesita atención» de «aquí no falta nada» y enlaza workbench, serie
  nueva y tablas de referencia.

Decisiones tomadas al implementar:

- **Los dos números de una tarjeta de sellos**: el plan pedía que «los números
  coincidan con el recuento del workbench filtrado», cosa que no puede pasar con
  las tres colas de sellos porque la rejilla cuenta series. La tarjeta enseña el
  número que cuenta y las series en las que están, y la comprobación es el par:
  sellos del informe = sellos de la tarjeta, series del filtro = total de la
  rejilla.
- **Las colas a cero se enseñan, pero no como trabajo**: una lista corta
  («Aquí no falta nada: Series sin país · …») para que se vea que un contador
  está a cero sin pintar seis tarjetas vacías. Si están todas a cero, un panel lo
  dice y desaparecen los enlaces filtrados.
- **El bug del filtro de imágenes se cierra aquí, no se documenta y se deja**:
  era el mismo contador respondiendo dos preguntas distintas, y el paso que las
  junta es este. Coste medido en los datos reales: 28 ms por recorrido con el
  índice cacheado.
- **El dashboard recorre el índice dos veces** (informe y filtro): 56 ms con la
  caché caliente, y por debajo del objetivo de 300 ms. Si algún día molesta, el
  arreglo es que `missing_data_report()` devuelva también el conjunto, no cachear
  la página entera a espaldas del usuario.
- **La fixture `dataset` de los tests se movió a `conftest.py`** para que el
  dashboard y el servicio comprueben los mismos números con los mismos datos, y
  la del workbench pasó a llamarse `grid_dataset` para no taparla (tenían formas
  distintas y el mismo nombre).

Verificado: `pytest datadesk` → **408 en verde**; suite completa **1424 en
verde** · catálogos recompilados (las seis etiquetas de tarjeta, el aviso de base
completa, los totales y el plural «en %(count)s serie/series») · **19 tests
nuevos** (la tabla de colas en las dos direcciones, los seis contadores contra un
recuento directo, los pares series/sellos contra el total de la rejilla, los
enlaces con su filtro, la base completa, los totales, el español y el acceso) ·
medido en los datos reales: **1.177 sellos sin imagen en 1.044 series**, 28 ms el
recorrido; el filtro viejo devolvía 2.542 de 2.543 series.

### S21 — Activity y revertir (2026-11-19)

`datadesk/activity.py` (lectura y revert), `views/activity.py`, la plantilla y su
JS:

- **`activity.py`**: `activity_page()` (commits paginados, dos consultas para la
  página), `changed_fields()`, `revert_order()` y `revert_commit()`.
  `revert_order()` es la pieza que hace que funcione: recreaciones con los padres
  primero, actualizaciones en medio, borrados con los hijos primero.
- **`views/activity.py`**: la lista y el POST del revert. Si el revert se
  rechaza, la respuesta es **la misma página con el motivo arriba** (409), no un
  JSON: el usuario estaba leyendo esa lista y el mensaje pertenece a ella. Si
  sale bien, redirección con `?reverted=<commit>` para no reenviar el POST.
- **`audit.record()`** gana `reverts_commit_id` (palabra clave), que es lo que
  enlaza el commit de vuelta con el revertido.
- **Plantilla**: un `<form>` por commit con su diálogo **generado en el
  servidor** (lista qué será de cada fila y avisa de los `CollectionItem`). El
  botón de confirmar es el `submit` y está dentro del diálogo: sin JavaScript no
  se revierte nada.
- El dashboard enlaza la pantalla, como con las tablas de referencia.

Decisiones tomadas al implementar:

- **Paginación por commit**: cortar por filas partiría un lote en dos y ofrecería
  medio revert. La consulta agrupa por `commit_id` y pide las filas de la página
  en una segunda consulta.
- **`cloned_from` no es una columna**: `changed_fields()` la salta. S17 la escribe
  en el `after` del clon como procedencia, y el log no puede presentarla como un
  campo de la serie (ni el revert pasarla a `Model(**snapshot)`: solo aparece en
  filas `create`, que se borran en vez de reconstruirse).
- **El revert de un `update` escribe el snapshot entero y toca `updated_at`**, no
  solo el valor que cambió: `auto_now` no se dispara con `update()` y el chequeo
  de conflicto de S12 compara esa columna. Hay test.
- **Recrear valida el id**: `save(force_insert=True)` con el id original, y un
  `IntegrityError` se convierte en 409 con el objeto nombrado en vez de un 500.
- **Un revert es un commit como cualquier otro**: se audita, se lista y por tanto
  se puede revertir (que rehace el cambio original). No se bloquea, porque
  bloquearlo obligaría a una excepción en el modelo; se documenta.
- **La etiqueta del sello va en singular** («Sello #12», «Serie #12»): el log
  habla de una fila, no de una tabla.

Verificado: `pytest datadesk` → **438 en verde**; suite completa **1454 en
verde** · catálogos recompilados (los verbos, los estados, el aviso de
colecciones y `Stamp`) · **30 tests nuevos**: lectura (un commit = una tarjeta,
orden, paginación por commit, campos cambiados, `cloned_from` fuera, estado de
fusión, orden de dependencia), revertir alta (serie y sellos, commit nuevo con
`reverts_commit_id`, filas originales marcadas, segundo revert 409, clon), revertir
borrado (ids y colores de vuelta, `CollectionItem` que **no** vuelven), revertir
edición (valores y `updated_at`, rename de lookup), los tres rechazos (cambiado
después, fusión, colisión de id), commit desconocido, y la pantalla (lista,
fusión sin botón, POST con redirección, banner, rechazo renderizado, acceso).

### S22 — Cierre (2026-11-19)

Cambios repartidos por lo que ya existía, más dos tests y el README:

- **`workbench.js`**: `typing()` (el atajo es de la pantalla, no del campo),
  `moveSelection(step)` (la selección como cursor, sin dar la vuelta en los
  extremos) y las teclas `/`, `j`, `k`, `N` junto al `Enter` que ya había.
- **`lookups.js`**: lo mismo con `/` y `j`/`k`; el cursor deja una fila
  seleccionada y no dos, porque dos es para fusionar.
- **Plantillas**: línea `dd-keys` bajo cada grid (traducida), `role="dialog"` en
  el panel de revisión y el `↺ Use last issue` con los valores que escribiría.
- **`issue_workspace.js`**: `prefillDiffers()`/`paintPrefill()` desactivan el
  botón cuando el formulario ya tiene esos valores (que es como carga), y
  `applyPrefill()` marca con `dd-applied` los campos que toca.
- **CSS**: `:focus-visible` para enlaces, botones y `summary` (y blanco en la
  barra oscura), `--dd-soft` a `#6b7280`.
- **`test_i18n.py`**: `PROSE_SINK`/`PROSE` y el test que recorre los scripts.
- **`test_service_read.py`**: la ordenación por fecha, ascendente y descendente.
- **`README.md`**: teclado, backup previo, apagar el flag y qué no devuelve un
  revert.

Decisiones tomadas al implementar:

- **`↺ Use last issue` se arregla aquí, no se documenta como raro**: el botón
  ahora dice lo que escribiría (`España · 1987`), está desactivado mientras el
  formulario ya lo tiene y parpadea los campos donde aterriza. Era el follow-up
  de S11 y una de las dos deudas del proyecto.
- **Los colores en `mode=edit` no entran**: necesitan que el change set lleve
  M2M, que es un cambio de fondo; se queda como hueco conocido en `progress.md`.
- **El contraste se arregla en el token, no en cada uso**: `--dd-soft` estaba a
  2,6:1 y era el color de todos los textos atenuados; oscurecerlo una vez es la
  única forma de que no vuelva a aparecer el problema al añadir una pantalla.
- **El test de i18n prohíbe prosa, no cadenas**: los selectores, las clases y los
  tres glifos son legítimos; lo que no puede aparecer es una frase donde se pinta
  texto, y el regex de «dos palabras seguidas» es lo bastante simple para
  entenderlo cuando falle.
- **`manage.py check --deploy` no cambia**: los 6 avisos son del proyecto
  (HSTS, redirección SSL, `SECRET_KEY`, `DEBUG` y las dos cookies seguras, que
  `DATADESK_TLS` pone en producción). Comprobado con el flag encendido y apagado.

Verificado: `pytest datadesk` → **441 en verde**; suite completa **1457 en
verde** · catálogos recompilados · arneses de jsdom: **79** comprobaciones en
`mode=new` (las 73 más el botón de prefill: nombre, desactivado, se activa al
cambiar, devuelve el valor y marca el campo), **74** en `mode=edit`, **14** en el
workbench (`j`/`k` con sus extremos, `/`, `N`, `Enter` y los guardas de foco) y
**6** en las tablas de referencia (`/`, `j`/`k`, una sola fila seleccionada).

### ✅ Primera tanda terminada (S1–S22)

Con la app en marcha, la primera revisión de uso real dejó cinco cosas que no son
de la primera tanda: están repartidas en **S23–S27** (ver §3, «Segunda tanda»),
de la más barata a la que menos se usa. No se mezclan en un paso porque son un
bug visual, un cambio de diseño, dos huecos funcionales y una puerta que existe
en otro sitio.

### S23 — El anillo del campo rechazado (2026-11-19)

Un bug de orden de pintado, no de clase: `.dd-cell-invalid` dejó de perder el
borde inferior. Causa y arreglo en el detalle del paso; dos tests en
`test_layout.py` sujetan la declaración.

### S24 — Escala tipográfica y ritmo (2026-11-19)

La app dejó de ser un interfaz de 12 px: cinco tokens y 52 reglas que pasan por
ellos, grid de 13 en filas de 36 con el cromo de Tabulator sustituido por los
tokens de la app, tarjeta de página más plana y el último migajón como título.
Detalle y decisiones en el paso; cuatro tests sujetan la escala.

### S25 — Borrar un sello, con su preview (2026-11-19)

Mismo patrón que el borrado de S17 aplicado a una fila: preview de ítems de
colección y de sellos hermanos, una fila de auditoría con el snapshot completo y
el revert de S21 devolviendo el sello con su id y sus colores (los
`CollectionItem` no vuelven). Detalle y decisiones en el paso.

### S26 — Nueva fila en las tablas de referencia (2026-11-19)

`New row` y `N` abren un diálogo de un campo que usa el endpoint de creación de
S18; el año lleva los mismos límites que la franja, un duplicado selecciona la fila
existente y la recién creada se resalta aunque haya caído en otra página.

### S27 — Moverse entre series y borrar desde la lista (2026-11-19)

`issue_positions()`/`neighbours_of_issue()` reutilizan la lista de pks de
`page_of_issue()`; los filtros viajan del workbench a la vista de serie y vuelven
en las flechas, el contador y el enlace de vuelta; `[`/`]` hacen lo mismo desde el
teclado. En la lista, el diálogo de S17 compartido en un partial, una columna `×`
por fila y `Supr` que solo abre el diálogo.

### ✅ Segunda tanda terminada (S23–S27)

Cinco pasos, ninguno mezclado con otro: el anillo (bug), la escala (diseño), el
borrado de un sello y la fila nueva (huecos funcionales) y la navegación con el
borrado desde la lista. Lo que sigue fuera, decidido y escrito en `progress.md`:
corregir los colores de un sello en `mode=edit` (necesita M2M en el change set).

### ⏳ S28 — Pulido visual (pendiente, sin prisa)

Cerrado el diseño el 2026-11-20 con tres maquetas del workbench en
`memory-bank/mockups/` (`workbench-compare.html` abre las tres apiladas): actual,
Bootstrap 5.3.3 y pulido sobre los tokens de S24. Bootstrap y Materialize quedaron
descartados con argumentos, no por gusto —el primero no reparte los anchos de la
tabla y el segundo es Material de 2014—, y el pulido son cinco cambios de CSS sin
dependencias. Detalle y aceptación en §4, S28.

### ✅ S29 — Ver la imagen y la descripción de un sello (2026-11-21)

La miniatura de 26 px dentro de filas de 38 no es una foto, y la descripción del
sello no se veía en ningún sitio. Se resolvió con un **panel a la derecha del
grid, atado a la fila seleccionada**: sin hover y sin clic sobre la imagen, y la
selección **no existía en esta pantalla** —`selectableRows` no estaba puesto y
`j`/`k` eran del workbench—, así que S29 los añade.

Decisiones al implementar:

- **La descripción no es una columna visible** (prosa en una celda de 13 px es un
  elipsis), pero sí una **columna oculta** (`visible: false`, `patch:
  "description"`): así `patchOf`, `fieldLabels`, `readValue`/`writeValue`, `sync`,
  el undo y el borrador de `localStorage` funcionan sin saber que hay un panel, y
  cambiar de sello no pierde lo escrito. `field_labels()` la recoge sola, así que
  la revisión la llama **Stamp description** («Description» ya es la de la serie).
- **`quietCell`**: el panel escribe en la celda con los eventos silenciados, y el
  undo también. Una pulsación no es un paso de undo, y el `cellEdited` de reemplazo
  ya no reengancha el undo a sí mismo (antes, cada `Ctrl+Z` empujaba una operación).
- **La base se toma de `previewStart`** (el valor al enfocar), no de
  `cell.getOldValue()`: esa es la del arranque de la página y hacía que la revisión
  dijera `— → texto`.
- **Selección que no es un toggle**: Tabulator deselecciona la fila al volver a
  pulsarla; `rowClick` la vuelve a seleccionar, porque el panel es «dónde estás».
- **`j`/`k`** mueven por id (dos llamadas devuelven componentes distintos para la
  misma fila) con guarda de campo y de diálogo abierto.
- En `mode=new` el panel también está: la fila es un borrador (`new-1` mientras no
  tenga nombre), la imagen es el placeholder, y la descripción entra en el draft y
  en el payload de create por `patchOf`. `render()` conserva la selección por id.
- **El selector S/M/L se descarta** en este paso: es densidad, no legibilidad, y a
  72 px una serie de 57 sellos son ~4.000 px de scroll.

Dos bugs **anteriores** aparecieron al probarlo en un navegador de verdad:

- **`mode=new` no pintaba ninguna fila**: `resize()` llamaba `grid.setData()` en el
  mismo tick que construye Tabulator y `_wipeElements` reventaba con
  `Cannot read properties of null (reading 'verticalFillMode')`. Ahora espera a
  `tableBuilt`. Reproducido también con el JS de `HEAD`, así que no era de S29.
- **`?rows=N` no se lee en ningún sitio** de la vista: `NewRowSettings()` se
  construye sin argumentos y el control enseña siempre 4. Anotado en
  `progress.md`; no se toca aquí.

Ficheros: `datadesk/service.py` (`description` en `serialize_stamp`),
`views/workspace.py` (columna oculta), `templates/datadesk/issue_workspace.html`
(panel), `static/datadesk/issue_workspace.js` (`selectableRows`, panel, `j`/`k`,
`quietCell`, arreglo de `tableBuilt`), `datadesk.css` (`.dd-grid-body` de dos
columnas, panel sticky, apilado por debajo de 1100 px), catálogos en/es y tests.

Verificado: **493 datadesk y 1509 backend en verde**; en Chromium a 1366 px la
imagen mide 258 px de ancho y no hay scroll horizontal, a 1024 px el panel pasa
debajo; `j`/`k` cambian la imagen, una descripción tipada cuenta 1 cambio y sale
en la revisión como `texto → texto ZZZ`, el undo la devuelve y deja el botón de
revisión desactivado; `mode=new` selecciona, escribe y deshace; sin errores de
consola.

### ✅ S30 — «Ver series afectadas» desde una tabla de referencia (2026-11-21)

El número de uso de una tabla de referencia era un callejón sin salida: contaba
algo y no dejaba verlo. Ahora es un enlace a la lista filtrada, y la lista dice
por qué está filtrada.

- **Cinco filtros nuevos** en `IssueFilters`: `printer`, `artist`, `paper_type`,
  `print_type` y `color`. Los cuatro primeros son columnas de la serie y van por
  `FILTER_FIELDS`; el color es del sello y va con `Exists`, como las colas de
  «necesita atención», porque un join multiplicaría filas y rompería el
  `Count("stamps")`. Un test con un sello de dos colores lo fija: la serie sigue
  contando 1 sello.
- **`FILTER_NAMES` es la lista única** (servicio, parser, formulario y script).
  `filters_from()` vive en `views/workbench.py` y la importa el endpoint del grid:
  había dos parsers y los filtros nuevos se habrían quedado a medias.
- **Los chips se pintan en el script**, desde el formulario: la página recarga el
  grid sin recargarse, así que unos chips del servidor se quedaban viejos al
  cambiar un filtro en la barra (visto en el navegador). Etiquetas traducidas en el
  config (`filterLabels`, `chipsText`), cada chip es un enlace a la misma página sin
  ese parámetro, más «Clear all».
- **El enlace dice series.** El color anota `Count("stamps__issue", distinct=True)`
  en la misma consulta: la celda dice «40 series» y el `title` sigue diciendo los
  sellos («Used by 50 rows») cuando difieren. Un año enlaza con `year_min` y
  `year_max` puestos a su número, porque el id de `Year` no es el año.
- **A 0 no hay enlace**: un enlace a una lista vacía es un callejón disfrazado.
- La barra de filtros pasa a siete `select` (el mayor, 300 colores): son tablas
  pequeñas y un `select` nativo no necesita script.

Ficheros: `service.py` (`IssueFilters`, `FILTER_NAMES`, `FILTER_FIELDS`,
`filter_issues`), `views/workbench.py` (parser único, opciones, etiquetas),
`views/workbench_api.py` (usa el parser), `views/lookups.py` (textos),
`lookups.py` (`series_counts`, `series_of`, `filter_url`, `series_usage`),
`templates/datadesk/workbench.html`, `static/datadesk/workbench.js` (chips),
`static/datadesk/lookups.js` (el número como enlace), `datadesk.css`, catálogos y
tests.

Verificado: **509 datadesk y 1525 backend en verde**; en Chromium, la tabla de
artistas enlaza con `?artist=60`, la lista abre con 1 serie y el chip «Artist: … ×»
que la quita vuelve a la lista completa; `?color=33` abre con el chip «Color:
Amarillo ×» y el contador coincide con el enlace (40 series / 40 issues); cambiar
el imprenta desde la barra pinta su chip sin recargar; a 1440 px sin scroll
horizontal.

### ✅ S30b — El workbench vuelve a caber en la pantalla (2026-11-21)

La primera revisión de S30 con el navegador encontró dos cosas que ningún test ve:

- **La barra creció y se llevó por delante la paginación.** Siete `select` en una
  barra flexible son cuatro filas (193 px), y el grid seguía con
  `height: calc(100vh - 300px)` —un número que S24 ajustó a dos filas—: a 1440×900
  el pie quedaba en y=899, fuera de la ventana. Ahora la tarjeta es una columna tan
  alta como la ventana (`calc(100vh - topbar - 64px)`) y el grid toma el resto con
  `flex: 1 1 auto` y `height: "100%"` en Tabulator, así que el pie está siempre
  dentro, con la barra cerrada (104 px), abierta (221 px) o con chips. Comprobado a
  1440×900, 1366×768 y 1366×600.
- **La fila de chips vacía ocupaba 17 px** porque `.dd-active-filters
  { display: flex }` vencía al atributo `hidden`; una regla global
  `[hidden] { display: none !important }` lo arregla en todas las pantallas (se
  comprobó que el panel de revisión y los diálogos siguen abriendo).
- **Los cinco filtros nuevos van detrás de «More filters»**, un `<details>` sin JS
  que se abre solo cuando uno de ellos filtra. La barra vuelve a su altura de antes
  y el control sigue a mano cuando hace falta.

Y el falso positivo que costó la tarde: **«los filtros no funcionan» era el
`workbench.js` anterior en el navegador**. Los `select` los pinta el servidor y los
lee el script, así que con el JS viejo la página enseñaba los filtros nuevos, la URL
llevaba el parámetro y la lista salía entera. Se arregló al recargar, y ahora no
puede repetirse en silencio: los assets de DataDesk llevan `?v=` con la fecha del
fichero más nuevo (`datadesk/context.py` + context processor), de modo que el
navegador los vuelve a pedir en cuanto cambian. En producción el manifiesto ya
hashea; el sello solo cubre el desarrollo y cualquier servido sin hash.

Ficheros: `views/workbench.py` (dos grupos de filtros, `extra_filters_open`),
`templates/datadesk/workbench.html` (el `<details>`), `datadesk.css` (columna,
`[hidden]`, desplegable), `workbench.js` (`height: 100%`), `datadesk/context.py`,
`_backend/settings.py` (context processor), `base.html` y las tres plantillas con
script, catálogos y tests.

Verificado: **517 datadesk y 1533 backend en verde**; en Chromium, 1366×768 con el
desplegable abierto deja el pie visible (y=700 en 768), `?printer=11` abre el
desplegable con el filtro puesto y su chip, quitarlo vuelve a 2.542 series, y elegir
artista dentro del desplegable filtra sin recargar.

### ✅ S28 — Pulido visual: tipografía, controles y elevación (2026-11-21)

Los cinco cambios, todos en `datadesk.css`, con la maqueta `workbench-polished.html`
como referencia:

- **Inter self-hosted**: la variable latin (48 KB, `wght` 100–900, 518 glifos) que
  sirve Google Fonts para `family=Inter:wght@100..900`; el fichero bajado es
  **byte a byte** el de la maqueta, así que la procedencia es verificable. Fila en
  `VERSIONS.md` con la versión real (4.001, leída de la tabla `name` con fontTools,
  no inventada) y su sha256; el fichero entra en la tupla de `test_assets.py`. El
  test de versiones baja a `\d+\.\d+` porque la fuente numera en dos componentes y
  las librerías en tres.
- **Controles**: 34 px, `--dd-line-strong`, hover y anillo suave
  (`--dd-ring`, 3 px al 12 %) en lugar del `outline` sólido con `-1px`. Se aplica a
  la barra de filtros, a la franja de la serie, al control de filas **y al login**,
  que tiene su propio `.dd-field input` al final del fichero. El `:focus-visible`
  sólido se queda para botones y enlaces: ahí el outline es la herramienta correcta
  y no lo tapa nada.
- **Movimiento**: `--dd-ease: 120ms ease` en botones, enlaces, filas e inputs, y un
  `prefers-reduced-motion` que lo apaga entero.
- **Elevación**: la tarjeta pierde el borde y usa `--dd-shadow-rest`, radio 12;
  los flotantes (diálogos, panel de revisión, columnas) comparten
  `--dd-shadow-float`. La **cabecera de la rejilla pasa a clara** (`#f8f9fb`, texto
  `--dd-muted`) y la fila seleccionada gana una barra de 2 px a la izquierda; las
  flechas de ordenación, que eran `#bbb`, se tiñen de `--dd-soft`.
- **Ritmo**: tokens `--dd-s1..s6`, fila de 38, `tabular-nums` en las celdas.

Dos cosas que no salieron como estaban escritas:

- **El `—` de las celdas vacías no puede ser solo CSS.** Tabulator escribe
  `&nbsp;` para un valor vacío, así que `:empty` no engancha nunca. Va un
  `emptyFormatter` en los dos scripts (workbench y sello) que devuelve un nodo de
  texto o el guion; el `:empty::after` se queda como red para las celdas cuyo
  formatter no pinta nada. Es la única línea de JS del paso y está explicada en el
  propio fichero.
- **Las cabeceras se cortaban** ("YE…", "DA…", "EDIF…", "FACE V…") porque las
  columnas se reparten con `grow` y no hay suelo. Se añaden mínimos reales
  (`year` 92, `date` 108, `stamps` 102 en el workbench; `edifil`/`fesofi` 94,
  `face_value` 122 en la rejilla del sello) y **"Total printed" pasa a "Printed"
  en la cabecera** ("Total printed" se queda como etiqueta del campo, con una clave
  `label` nueva en la columna, para no degradar el panel de revisión). Medido: a
  1440 no se corta ninguna cabecera y no hay scroll horizontal; a 1366 con el panel
  de S29 abierto solo se acorta la cabecera de la tirada, que es el precio de que
  el panel ocupe 280 px.

Ficheros: `datadesk.css` (tokens, fuente, controles, sombras, cabecera, ritmo),
`vendor/inter-latin-var.woff2`, `vendor/VERSIONS.md`, `views/workbench.py` y
`views/workspace.py` (mínimos y la etiqueta), `workbench.js` e
`issue_workspace.js` (`emptyFormatter`), `tests/test_assets.py`,
`tests/test_layout.py` (seis pines del nuevo look) y `tests/test_workspace*.py`.

Verificado: **524 datadesk y 1540 backend en verde**; en Chromium a 1440×900 y
1366×768: Inter cargada (`document.fonts.check`), cabecera clara, fila de 38,
tarjeta sin borde, pie de paginación dentro (S30b intacto), anillo de foco en un
campo, guion en 78 celdas vacías del workbench y 57 de la serie, y capturas de
workbench, panel de filtros, workspace, lookups, dashboard, actividad y login.

### ✅ S28b — La revisión de S28 en la app (2026-11-21)

Cinco cosas que solo se ven usando la pantalla:

- **La fecha del workbench se cortaba.** El `buildColumn` del workbench nunca copió
  `width` (solo `align`/`grow`/`min`), así que la columna no tenía más defensa que
  su `min` y `fitColumns` la repartía a su gusto. Ahora `date` lleva **ancho fijo**
  de 112 px (una fecha tiene una longitud y no debe encogerse por lo que el usuario
  encienda en el menú de columnas) y el `buildColumn` del workbench entiende
  `width`. Medido a 1024, 1366, 1600 y 1920: 112 px y sin recorte.
- **La línea de atajos del workbench tocaba el borde.** Es hija directa de una
  tarjeta con `padding: 0`, así que estrena `padding: 0 var(--dd-s4)` y margen
  inferior.
- **La tarjeta del workbench no terminaba en esquinas redondeadas**: el grid raíz de
  Tabulator es `#888` por defecto y solo las filas lo tapaban, dejando una banda
  gris cuando la serie tiene un sello. `#workbench` y `#stamp-grid` llevan
  `background: var(--dd-surface)`.
- **La tarjeta de la serie tenía las esquinas cuadradas**: su franja tiene fondo y
  pintaba su esquina sobre el radio. Se redondean la franja (arriba) y la barra de
  commit (abajo) en vez de poner `overflow: hidden` en la tarjeta, que recortaba 12
  px del desplegable del editor de colores de la rejilla.
- **La × de borrar serie no estaba centrada.** El botón del workbench usaba
  `.dd-row-delete-action`, que no tenía caja: un glifo de 16px sobre la línea de
  texto se queda arriba en una fila de 38, aunque la columna esté centrada. Ahora
  usa la misma `.dd-remove` que la × del sello (caja de celda completa), y el
  chevron de abrir se centra igual con flex, que tenía el mismo problema.
- **La moneda no aparecía en ningún sitio.** Las columnas `mnh`/`used` de los dos
  grids llevan `money: true` y un formatter que escribe `1.20 €` (con `min: 104` en
  el workbench, que `37500.00 €` son diez caracteres); los campos de la franja y las
  etiquetas del panel de revisión dicen `(€)` con una clave `unit` en
  `SERIES_FIELDS`. El símbolo va en el valor y no solo en la cabecera porque el
  mockup lo mostraba así.

Ficheros: `datadesk.css`, `workbench.js` (`width` y `moneyFormatter`),
`issue_workspace.js` (`moneyFormatter`), `views/workbench.py` y
`views/workspace.py` (`width`, `money`, `unit`), la plantilla de la serie y tests.

Verificado: **526 datadesk y 1542 backend en verde**; capturas a 1024-1920.

### ✅ S33 — Añadir un sello a una serie existente (2026-11-22)

La operación que faltaba, encontrada haciendo el trabajo y no revisando el estilo.
`+ Stamp` en la barra de `mode=edit` añade una **fila borrador** a la rejilla:
nace con `new-<n>`, vive en el change set como cualquier otro cambio y se escribe
al commitear. El backend no se tocó: `/apply` ya aceptaba `op: "create"` para un
sello de una serie existente.

Decisiones tomadas al implementar:

- **El id se reconcilia**. `entryFor()` marca `op: "create"` para una fila de
  `newRows` y `sync()` la escribe entera (los ocho campos, más `issue`) en vez de
  diferenciarla contra una `base` que no tiene. Al volver el commit, `adoptDraft()`
  cambia el id de la fila por el real y le pone `updated_at` y sus dos URLs.
- **Las dos URLs de una fila nueva las da el servidor como forma**, no el script:
  `url_template()` reversea la ruta con una sonda y deja `%(id)s` donde va el id
  (`/datadesk/stamps/%(id)s/delete/`). Componer la ruta en JS habría sido una
  segunda fuente de verdad; un test sustituye un id real y compara con `reverse()`.
- **Commit limpio = recarga de la misma serie**, no vuelta al workbench. Recargar
  es lo que convierte el borrador en fila guardada: id real, URLs, imagen que el
  servidor sabe encontrar y contador correcto. `?focus=` del workbench sigue
  existiendo como enlace directo, pero ya no lo escribe nadie.
- **Un commit parcial sí reconcilia en caliente**: las filas escritas se adoptan y
  las rechazadas se quedan con su mensaje, así que reintentar no vuelve a crear el
  sello que ya entró. Probado en el navegador con una fila buena y una rechazada
  en el mismo lote: la adoptada se puede editar después y su × abre el diálogo
  real de S25.
- **Añadir y quitar son pasos de historial distintos** (`create` / `remove`), porque
  son operaciones inversas: `Ctrl+Z` quita la fila recién añadida y devuelve la que
  se acaba de quitar con lo que tuviera escrito. Costó un intento: con un solo
  `create`, deshacer una eliminación volvía a eliminar.
- **Una fila sin tocar no es un sello**: `dropBlankDrafts()` la quita al commitear.
  «Sin tocar» significa que el nombre sigue siendo el de la serie (que es un
  valor por defecto, no contenido) y ningún otro campo tiene nada.
- **El × de un borrador no pregunta**: no existe en la base, así que se quita con
  una entrada de historial y no abre el diálogo de S25 (`dd-row-new` mantiene el ×
  activo aunque la rejilla esté bloqueada por el change set).
- **No viaja en `localStorage`**: un `create` no tiene `base`; el borrador guarda
  solo `update`, igual que `mode=new` no guarda nada. El `beforeunload` sí avisa,
  porque la fila está en el buffer.
- **La revisión lo lista como nuevo**: sin `before → after`, con un chip `NEW`
  (texto del servidor) y solo los campos que llevan algo; el contador cuenta la
  fila como **un** cambio, no como nueve campos.

Verificado en Chromium con la serie de 1976: añadir → revisión → commit parcial
(una fila creada, otra rechazada por `face_value` en blanco) → editar la creada →
arreglar la rechazada → commit limpio y recarga con las dos filas guardadas; el
contador y el × acompañan. 16 tests nuevos (14 de la pantalla en
`test_workspace_add_stamp.py` y 2 pins de CSS en `test_layout`); 545 datadesk y
1561 backend en verde.

### ✅ S29b — La placa de la imagen del sello (2026-11-22)

Los WebP del árbol son RGBA con el sello recortado (alpha 0 en las esquinas), así
que el fondo lo pone la pantalla — y el panel de S29 lo pinta **blanco**
(`.dd-preview-image { background: #fff }`). La mayoría de los sellos tienen marco
blanco: sobre blanco el dentado desaparece y la pieza se ve como un cuadrado.

Va aparte de S29 porque no es la lógica del panel sino una placa: una superficie
gris neutra con un hairline detrás de la imagen (y detrás de la miniatura de 26 px,
que se apoya en la fila blanca). La regla es de producto, no solo de DataDesk: la
app pública de Flet enseña las mismas imágenes y tiene el mismo problema.

La placa es `--dd-plate`, un token, y la usan los dos tamaños: el panel y la
miniatura de 26 px. Se probaron tres grises en el navegador (`#d7dde5`, `#cfd6df`,
`#c2cad4`) y se quedó **`#cfd6df`**: el primero casi no se distingue del blanco del
marco y el tercero convierte la placa en un bloque. El borde va con un token propio,
`--dd-plate-edge` (`#b6c0cc`): más claro que la placa parece un halo, y estas
imágenes ya traen su propio margen blanco. En el panel va de borde; en la miniatura
es un `box-shadow` y no un `border`, porque a 26 px dos píxeles de borde son dos
píxeles de sello. Tres tests lo fijan (el token no es blanco, los dos tamaños
comparten la misma placa, la miniatura no pierde píxeles).

Verificado en Chromium con la serie de 1976 (sello de marco blanco): el dentado se
distingue en el panel y en las miniaturas, incluso a 26 px; 529 datadesk en verde.

### ✅ S35 — Cambiar los colores de un sello desde el panel de la imagen (2026-11-22)

El hueco que la app arrastraba desde S18, cerrado. El backend ya estaba entero
(`/apply` acepta `colors` en un `update`, el snapshot guarda la M2M como ids y el
revert la devuelve); lo que cambió es la pantalla y el idioma en que la fila habla.

Decisiones tomadas al implementar:

- **Los ids son el único idioma del color.** `serialize_stamp()` manda
  `[pk, pk]` ordenados por nombre en vez de `{name, tone}`, y el nombre y el tono
  salen de la paleta que viaja en la página. Con eso el valor de la celda, el
  patch, el borrador, la revisión y el deshacer dicen lo mismo, y no hay una
  traducción id→nombre por el medio que se pueda desincronizar.
- **La paleta viaja en los dos modos.** Es la excepción consciente a S18: un
  editor de varios valores necesita sus opciones y un chip necesita el tono de un
  id. Cuesta **una consulta más** en la pantalla de la serie (la paleta), que no
  depende del tamaño de la página: el test de S9 pasó de 1 a 2 consultas de color y
  lo dice. Y cuesta **peso**: con los datos reales son **300 colores**, no las
  «decenas» que el diseño suponía, o sea unos 18 KB de JSON por pantalla (nginx los
  comprime). Se acepta para un usuario en una LAN; si molesta, la salida está
  escrita en §4: un endpoint con ETag y `editorParams.values` como promesa.
- **El panel es el widget, la celda no.** La columna de colores lleva
  `patch: "colors"` solo en `mode=edit` —para que el change set sepa el campo— pero
  `buildColumn` no le pone editor (un `input` convertiría una lista de ids en una
  caja de texto) y en `mode=new` conserva el `list` de la fila rápida. El campo del
  panel **no** es un `data-lookup`: `unresolvedLookup()` bloquea el commit con un
  nombre sin fila, y aquí un nombre sin fila se crea, no se rechaza. Hay un test que
  lo fija.
- **El control es el mismo en los dos modos.** En `edit` escribe la celda, hace
  `sync` y empuja un paso de historial; en `new` escribe la celda y actualiza el
  borrador de la fila. Verificado en `mode=new` provocando un `render()` (teclear en
  el nombre de la serie): el color sobrevive, así que el borrador lo tiene de verdad
  y el `create` lo enviará.
- **Teclear y commitear no pierde nada**: `flushTypedColour()` mete el color escrito
  (si existe) antes de commitear o de crear la serie. Sin eso, escribir «Rosa» y
  pulsar `Shift+Enter` lo habría tirado en silencio.
- **El tercer arreglo del pase**: la celda de un sello sin colores pintaba vacío y
  ahora pinta el `—` de S28 — en los datos reales hay 1.648 sellos así.
- **El panel `New colour` de la barra se queda** (decisión del usuario): crea un
  color sin seleccionar un sello, y las dos puertas comparten la paleta con
  `addToPalette()`, que también alimenta la lista del editor de la fila rápida.
- **Los nombres para la revisión y el deshacer** se siembran del mapa de lookups con
  la paleta, así que un borrador restaurado de `localStorage` enseña nombres.

Verificado en Chromium con la serie de 1976: añadir un color escribiendo (chip, «1
change», `Castaño +2` en la celda), quitarlo con su ×, `Ctrl+Z` de las dos cosas
(una entrada cada una), la revisión con `Castaño · Pizarra → Castaño · Pizarra ·
Rosa`, commit y recarga con el color guardado, la serie restaurada a su estado
anterior y deshacer con `Ctrl+Shift+Z`. Además: una serie con un sello sin colores
(panel con «No colours.» y la celda con `—`), `+ Create "Prueba S35"` creando el
color y asignándolo en el mismo gesto, y `mode=new` con el `list` de la celda
todavía abriendo (Tabulator 6 lo pinta con `.tabulator-edit-list-item`, no con
`.tabulator-list`, que es lo que yo buscaba al principio).

Tests: 13 nuevos — 8 en `test_workspace_colours.py` (ids en la fila, orden por
nombre, lista vacía, la paleta con nombre y tono, los controles del panel, el campo
que no es un lookup, el mismo control en `mode=new`), 3 en `test_write.py` (cambiar
los colores, vaciarlos, un id que no existe), 1 en `test_activity.py` (el revert
devuelve los colores, la rama `_restore` que no estaba cubierta) y 1 de la columna
partida en dos en `test_workspace_edit.py`. 558 datadesk y 1574 backend en verde.

### ✅ S36 — El orden de la lista lo decide el código de la serie (2026-11-22)

Bug de uso, no de estilo: con la misma fecha y el mismo nombre, el orden lo decidía
la base. Ahora `issue_queryset()` anota `first_code` (`Min` del código Fesofi de
sus sellos, con Edifil como respaldo por sello) y todas las ordenaciones terminan en
`(longitud del código, código, nombre, pk)`.

- **Fesofi, no Edifil**, aunque Edifil se enseñe primero en el grid: los datos
  mandan. Edifil falta en el 29% de los sellos y en 696 series; Fesofi en 61 sellos
  y 6 series. El respaldo por sello evita que dos catálogos se mezclen en una misma
  serie.
- **Longitud primero**: en el grupo del 29-12-1998 conviven códigos de hoja (3649) y
  de emisión (1998042); ordenar como texto pondría el especial el primero, y
  numéricamente el 3649 es menor. Con longitud + texto, el especial queda al final.
- **El `pk` al final** no es adorno: es lo que hace el orden total y lo que impide
  que dos páginas se solapen. Hay un test que pagina de una en una y comprueba que
  no se repite ninguna fila.
- **`issue_positions()` no tenía la anotación** y ahora la necesita (ordena por
  `first_code`): se le añade con `with_catalogue_key()`, y así las flechas de la
  serie y el contador `4 / 2.541` caminan exactamente la lista que se ve.
- Medido en Postgres con los datos reales: 65 → 68 ms la página del grid, los
  contadores del panel igual (20 ms) y `issue_positions()` 2 → 8 ms. Sin índice.
- 7 tests nuevos en `test_service_read.py` (el código manda sobre el nombre, el más
  corto primero, sin código al final, el respaldo Edifil, una ordenación por columna
  que también acaba en el código, el orden total al paginar y las posiciones
  coincidiendo con el grid). 565 datadesk y 1581 backend en verde.

### ✅ S37 — Un control tiene el mismo aspecto en cualquier sitio (2026-11-22)

El campo de color del panel y su descripción se pintaban como controles del
navegador al lado de una tira de campos con el estilo de la app. La causa no era
el panel: el aspecto de un control estaba declarado en `.dd-field .dd-input`, así
que **dependía de ir dentro de una etiqueta de la tira**. Había tres copias del
mismo bloque (`.dd-field .dd-input`, `.dd-rows .dd-input` y `.dd-filter input`) y la
cuarta —el panel— no existía.

- El bloque pasa a `.dd-input`, sin prefijo, y las dos copias que solo repetían
  geometría se quedan con lo que las hace distintas: el control de filas, su ancho
  y su alineación; la barra de filtros, sus `select` y el chevron propio.
- Un `textarea.dd-input` gana relleno vertical (`var(--dd-s1)`): con el relleno de
  una línea, la primera línea tocaba el borde. Se nota en la tira y en el panel.
- El panel deja de forzar `display: block` en su campo de color: usa el mismo
  `.dd-lookup` que la tira, así que el `+ Crear "X"` cae debajo del campo igual.
- Medido en el navegador: 34 px de alto, radio 8, borde `--dd-line-strong`, 13 px
  Inter y el mismo relleno en los cuatro campos (nombre y descripción de la tira,
  color y descripción del panel). Y el campo de referencia de la tira, enfocado con
  la lista cargada, enseña la misma flecha nativa que el del panel: no había dos
  estilos, había uno a medias.

Tres pins en `test_layout` (el look no está dentro de `.dd-field`, la base lleva la
geometría, el textarea lleva relleno vertical). 568 datadesk en verde. Sin cambios
de plantilla ni de JS: dos controles llevaban la clase correcta desde S29/S35 y no
les llegaba el estilo.
