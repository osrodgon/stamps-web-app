# DataDesk — rendimiento e índices (S9)

Medido el **2026-11-18** contra la base real de desarrollo: **2.540 series**,
**9.558 sellos**, la serie más larga con **57 sellos**. Repetir estas cifras
después de S14 (edición en línea) y de S16 (change set) para comparar.

## Método

Scripts ejecutados dentro del contenedor de backend con `manage.py shell`:

- tiempos: 10 repeticiones por escenario, con `min` / `mediana` / `p95` / `max`
  (con 10 muestras el `p95` es la novena, no la primera);
- contador de queries: `CaptureQueriesContext`, que fuerza el cursor de debug;
- planes: `QuerySet.explain(analyze=True, buffers=True)`, más
  `pg_indexes` para el inventario real de índices.

## Tiempos (página de 100 filas)

| Escenario | min | mediana | p95 | max | queries |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primera página | 67,4 | 68,2 | **70,3** | 73,9 | 2 |
| Última página (offset 2.500) | 66,9 | 67,5 | **71,5** | 74,1 | 2 |
| Filtro por año 1950–1960 | 43,2 | 44,3 | 45,4 | 46,6 | 2 |
| Búsqueda de texto `real` | 33,9 | 35,0 | 37,0 | 39,3 | 2 |
| Orden por país (desc) | 66,2 | 67,3 | 68,7 | 70,2 | 2 |
| Orden por nº de sellos (desc) | 65,9 | 67,5 | 69,8 | 69,9 | 2 |
| `attention=no_country` | 10,4 | 10,6 | 11,5 | 12,5 | 2 |
| `attention=no_date` | 10,8 | 11,7 | 12,0 | 12,3 | 2 |
| `attention=no_stamps` | 58,8 | 59,4 | 61,7 | 62,4 | 2 |
| `attention=stamps_without_colors` | 79,5 | 81,8 | **84,1** | 84,6 | 2 |
| `attention=stamps_without_face_value` | 48,3 | 49,2 | 49,7 | 53,7 | 2 |
| `attention=stamps_without_image` | 74,8 | 77,1 | 79,8 | 79,8 | 2 |

Sellos de la serie más larga (57 sellos): **3,2 ms de mediana, 2 queries**
(la de sellos + la de colores).

Contador de queries con `size` = 10 / 50 / 100 / 200: **2 / 2 / 2 / 2**
(`COUNT` + página). No hay N+1 en ningún escenario.

**Aceptación**: p95 < 300 ms → se cumple con margen (el peor caso son 84 ms).
La última página no se degrada frente a la primera (71,5 vs 70,3 ms de p95).

## Dónde se va el tiempo

El plan de la primera página dice:

```
Limit (actual time=23.7..23.8 rows=100)  Planning Time: 42.4 ms  Execution Time: 24.0 ms
```

- **`Planning Time` ≈ 40 ms, `Execution Time` ≈ 24 ms**. El coste no es leer la
  tabla: es planificar un join de ocho tablas con filas de 2.350 bytes.
- Confirmado por otra vía: la misma SQL lanzada a pelo por un cursor tarda
  **59,9 ms** y por el ORM **62,3 ms** — el ORM y la serialización de 100 filas
  cuestan ~2 ms; el resto es Postgres.
- El `Count("stamps")` obliga a un `GroupAggregate` sobre las 9.558 filas del
  join de sellos, y el orden por defecto acaba en un `top-N heapsort` de 177 kB.
  A este volumen ambos son baratos.
- El `COUNT` de la paginación es aparte y cuesta **2,8 ms** de mediana.
- La búsqueda de texto baja a **2 ms de ejecución** porque filtra antes de
  agregar: `Seq Scan` de `Issue` (1,2 ms) y `HashAggregate` de lo que sobrevive.
- El filtro por año **sí usa el índice de la FK**:
  `Index Scan using issues_api_issue_year_id_d1f0e353`.
- La cola más lenta (`stamps_without_colors`) hace `Hash Semi Join` contra un
  `Seq Scan` de los 9.558 sellos: 32 ms de ejecución, 4.218 series candidatas
  antes del límite.

## Inventario de índices (lo que ya hay)

- `issues_api_issue`: pkey, las 7 FKs (`year_id`, `country_id`, `stamp_type_id`,
  `print_type_id`, `printer_id`, `artist_id`, `paper_types_api_id`) y
  `updated_at` (S5).
- `stamps_api_stamp`: pkey, `issue_id` y `updated_at` (S5); la M2M de colores
  tiene índice por `stamp_id` y por `color_id`, más el único de la pareja.
- Los 8 lookups: pkey + índice único de nombre + índice `*_like` de Django.
  `Issue.name` **no** tiene índice; `Stamp.face_value` e `image` tampoco.

## Decisión: **no se añade ningún índice**

Ninguno de los candidatos cambia los números y algunos no pueden usarse. Lo que
se descarta y por qué:

| Candidato | Veredicto | Motivo |
| --- | --- | --- |
| `Issue.name` | descartado | `name__icontains` se compila a `UPPER(name::text) LIKE UPPER('%real%')`; un btree no sirve con el comodín inicial. Haría falta `pg_trgm` + GIN, y hoy la búsqueda tarda **2 ms** |
| `(year_id, date)` | descartado | el orden por defecto ordena por `year.year` a través del join, no por `year_id`; el filtro por año ya usa el índice de la FK y el `top-N heapsort` de 2.540 filas es parte del plan barato |
| `Issue.country`, `Issue.stamp_type` | ya existen | son FKs, `db_index=True` |
| `Stamp.face_value` parcial (`= ''`) | descartado | las tres colas de sello son semi joins sobre 9.558 filas (32–49 ms de ejecución); a este volumen el `Seq Scan` gana a cualquier índice parcial |
| `Stamp.image` | descartado | misma razón, y la columna puede ser NULL o cadena vacía, así que ni un índice parcial simple cubre el caso |
| `updated_at` | ya existe | lo puso S5 para el control de conflictos de S12, no para lectura |

Ni siquiera hay una migración que hacer: el esquema se queda como está.

## Cuándo volver a mirar

Reabrir esta decisión si:

- el `p95` de la primera página pasa de **150 ms** o el de cualquier cola de
  **300 ms**;
- el volumen se multiplica por diez (~25.000 series). Ahí el primer candidato
  deja de ser un índice y pasa a ser **adelgazar el join**: menos
  `select_related` y un `COUNT` sin agregado, porque el problema es el tiempo de
  planificación, no el de lectura;
- la búsqueda de texto pasa de ~20 ms: entonces `pg_trgm` + GIN sobre
  `Issue.name`, con la extensión instalada a mano en la migración.

## Nota para S10

La serie más larga real tiene **57 sellos**, no 24 como decía el plan. El
workspace no pagina sellos por diseño (`stamp_queryset()` son 2 queries y
3,2 ms), así que 57 filas se pintan de sobra; el fixture de 100 sigue sirviendo
como comprobación de que no hay ningún techo escondido.

## Reproducir

```bash
sg docker -c "docker compose -f backend/docker-compose.yml \
  -f backend/docker-compose.dev.yml exec -T stamps-backend python manage.py shell" \
  < script_que_llama_issue_page_y_capture_queries.py
```
