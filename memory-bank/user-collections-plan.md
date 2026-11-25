# Normal-user collections: the reading screens

> **Status**: plan closed 2026-11-23, **implementation not started** — resume at §9
> **Audience**: authenticated normal users (`is_admin = false`)
> **Goal**: a user opens the app and walks their own collection — collections →
> series (paginated) → series detail with its stamps — editing **only** the fields
> that describe their own copy. Series and stamps belong to the catalogue and are
> read-only here.
>
> Mockups (open them in a browser, they use the real stamp pictures from
> `frontend/assets/stamps/`):
> `memory-bank/mockups/collections-overview.html`,
> `collection-series.html`, `collection-series-detail.html`.

---

## 1. What exists today

**Frontend** (Flet 0.84):
- `pages/collection/collections_page.py` is a skeleton: header, drawer, an empty
  `ft.Column` with the title. `main.py` registers it at `/collections` and the
  form's router is an exact-match dict (`ROUTE_HANDLERS`), unknown path → 404.
- The pieces to reuse are already there: `StandardPage` (header + main + drawer),
  `AppDrawer`, `YearRangeSelector`, `TablePagination`, `fmt_currency` in
  `core/utils.py`, `_()` from `core/translations.py`, and the stamp pictures:
  `components/table/issue_detail/stamp_card.py` resolves
  `assets/stamps/<year>/<fesofi>.webp` with `os.path.exists` and falls back to
  `no_stamp.webp`. **The images are local to the frontend**, so no card needs an
  image URL from the API.
- Locale keys `collections.title` and `collections.no_issues_found` exist. The
  rest of the keys this feature needs must be added by the user: the JSON files
  under `assets/locales/` are user-managed and are never edited by the agent.

**Backend** (Django + DRF):
- `collections_api.Collection`: `user` (FK `users_api.UserCollection`), `name`.
  No timestamps.
- `collection_items_api.CollectionItem`: `collection`, `stamp`, `location`,
  `condition_type`, `price_paid`, `acquisition_date`, `note`, `quantity`.
  `unique_together = (collection, stamp)` — one row per stamp per collection, so
  duplicates are counted in `quantity`.
- Endpoints: `GET /api/v1/collections/` (and `/<pk>`, create), `GET
  /api/v1/collection-items/` (and `/<pk>`, create). **What is wrong with them**:
  1. they return `Collection.objects.all()` / `CollectionItem.objects.all()` —
     every user's data, with no ownership check at all;
  2. `?username=` is declared in the schema of `CollectionsView` and then
     ignored — and it is not the way in either: the token says who is asking
     (D0);
  3. creating a collection relies on `X-API-KEY` being the user's
     `password_hash` (`# TODO. This need to be fixed`);
  4. no counts, no pagination, no "the series of a collection" and no
     "the stamps of one series with my copy".
- Authentication: the public API uses `CustomAPIKeyAuthentication` +
  `HasSpecificKeyName`, i.e. **one master key** shared by the app
  (`API_MASTER_KEY` in the Flet settings). The JWT that the login issues is not
  accepted anywhere. `common/core/jwt_token.py` already validates it and returns
  `user_id`, and `users_api.UserToken` exists.
- Data volume: 2.540 series, 9.555 stamps, 88% with a picture.

---

## 2. The three screens

1. **Collections** — `/collections`. A card per collection: cover (one of its
   stamps), name, `N series · M stamps`, and a completion bar (stamps owned /
   stamps in those series). `+ New collection` and the empty state.
2. **One collection** — `/collections/<id>`. Its series, **paginated server-side
   (a must)**: thumbnail, `year · date`, name, country and stamp type,
   `3 of 5 stamps · 60%` with a bar, `paid` and `catalogue (MNH)`, and a chevron
   into the third screen. A search box and a year range, reusing
   `YearRangeSelector`.
3. **One series** — `/collections/<id>/issues/<issue_id>`. The series header as
   the admin shows it (name, `Mint` / `Used` / `Printed` pills, date, the eight
   catalogue fields, description and notes) **without** the edit and delete
   icons, plus a badge saying the catalogue data is read-only. Below, one card
   per stamp of the series: picture, FESOFI/Edifil, face value, colour, catalogue
   values, and — the only editable part — **“Your copy”**: condition, quantity,
   price paid, acquisition date, location, note, with Save / Cancel / Remove from
   collection. A stamp the user does not own appears dimmed with `Add my copy`
   (see D2).

Navigation needs routes with a parameter, so `main.py` grows a small resolver:
`/collections` (exact, as today), `/collections/<int>` and
`/collections/<int>/issues/<int>` by prefix match, keeping `ROUTE_HANDLERS` for
the rest. `push_route` + `on_view_pop` already handle the browser back button.

---

## 3. Decisions

All closed on 2026-11-23; the plan is ready to implement step by step (§6).

| # | Decision | Closed |
|---|---|---|
|---|---|---|
| D0 | **How the API knows the user.** | **Closed 2026-11-22: the JWT the login returns.** The collection requests send `Authorization: JWT <token>` (`USER_JWT_TOKEN`, stored by `core/base_ui.py` at login), which is what `HasSpecificKeyName` already understands: its `JWT` branch validates the token and the view must be listed in `USER_VIEWS` (the four collection views already are). Without the header, or with a bad or expired token, the API answers **403** — that is today's behaviour, not a new rule. The user is taken from the token itself: `JwtToken.validate()` returns `user_id`, `username`, names and email, so **no `?username=` is needed** and no query parameter can lie about who is asking. The catalogue endpoints keep the master key. |
| D1 | **Can the user create / rename / delete a collection?** | **Closed 2026-11-22: yes.** A `CollectionForm` dialog with the name only, for create and rename, and a delete that warns with the counts of what goes with it (series and stamps of *their* rows; the catalogue is untouched). Without it a new user could never fill the page. |
| D2 | **Can the user add a stamp to a collection, or remove their copy?** | **Closed 2026-11-22: yes, and only their copy.** `Add my copy` creates a `CollectionItem`; `Remove from collection` deletes it. The catalogue (series and stamps) is **admin-only**: a normal user's token is accepted only on the views listed in `USER_VIEWS`, which is why these screens send the JWT and the admin screens keep the master key. The catalogue browser with “select all stamps in a series” stays a later phase. |
| D3 | **Which “Your copy” fields are editable?** | All six. `condition_type` and `location` are **selects** from their tables (read-only lists for the user); `quantity` ≥ 1; `price_paid` with two decimals; `acquisition_date` with the existing `DatePickerField`; `note` multiline. |
| D4 | **What does a collection card show?** | **Closed 2026-11-23: a collage of up to six stamps**, plus the name, `N series · M stamps` and the completion bar. The six are **stable**, not random on every load (a card that shuffles is a card you stop recognising): the API sends up to **12** of the collection's stamps in catalogue order and the frontend paints the first **six whose file exists** — the picture lives in the frontend's tree, so only it knows. A collection with no stamps (or with none of its pictures) shows `no_stamp.webp`, greyed like the admin does. Layout: one stamp centred and big, two to six as a mosaic of three columns; no empty holes. The covers of a whole page come in **one** query, not one per card. |
| D5 | **What does a series card show?** | **Closed 2026-11-23:** thumbnail, `year · date`, name, country and stamp type, `3 of 5 stamps · 60%` with the bar, **paid** (sum of `price_paid` of the user's items) and **catalogue (MNH)** (sum of the series' stamps). Two figures because they answer two questions: what it cost me and what the catalogue says it is worth. To be refined later with real data. |
| D6 | **Pagination** | Server-side, **15 series per page** by default (same as the admin table), selector 15/30/50, reusing `TablePagination`. Never load a whole collection. |
| D7 | **Default order of the series** | **Closed 2026-11-23:** year ascending, then date (nulls last), then the series' catalogue code — the total order DataDesk got in S36, so two series of the same day never swap between pages. Selector `Year ↑`, `Year ↓`, `Name`. |
| D8 | **Do stamps I don't own appear in the series?** | **Closed 2026-11-23: yes, dimmed**, with `Add my copy`. The progress bar needs its denominator and “what is missing” is half the reason to open a collection. |
| D9 | **Search and filters inside a collection** | Name search plus year range in the first version (both cheap server-side); country/stamp type later. |
| D10 | **Money on screen** | `fmt_currency` (already used by the admin), Spanish grouping (`37.500,00 €`), from the raw decimals the API sends. |

---

## 4. Backend: what is missing

All of it under `/api/v1/`, with **`Authorization: JWT <token>`** (D0) and scoped
to the user the token carries; every endpoint answers 404 (not 403) for a
collection that is not theirs. The response envelope, the `page` / `pageSize` /
`sortBy` / `order` parameters and the `pagination` block are the ones the
catalogue endpoints already use, so `TablePagination` and the existing services
keep working unchanged.

The first thing to add is a small helper — `current_user(request)` in `common` —
that reads the header, calls `JwtToken().validate(token)` and returns the
`UserCollection`; DRF's `request.user` is `None` today because
`CustomAPIKeyAuthentication` returns the key, not a user. The collection views use
it instead of `Collection.objects.all()`.

```
GET    /api/v1/collections/
       → [{id, name, series, stamps, owned, total,
           covers: [{year, code}, …up to 12]}]
       (counts and covers for the whole page in one query each, never one per card)

GET    /api/v1/collections/<pk>/
POST   /api/v1/collections/            {name}
PATCH  /api/v1/collections/<pk>/       {name}
DELETE /api/v1/collections/<pk>/       (the items go with it, by cascade)

GET    /api/v1/collections/<pk>/issues/?page=&pageSize=&name=&year=&sortBy=&order=
       → {data: [{id, year, date, name, country, stamp_type,
                  total_stamps, owned_stamps, paid, catalogue_mnh}],
          pagination: {page, page_size, total_count, total_pages}}

GET    /api/v1/collections/<pk>/issues/<issue_pk>/
       → {issue: {…the 15 catalogue fields…},
          stamps: [{…stamp…, item: {id, condition_type, quantity, price_paid,
                                    acquisition_date, location, note} | null}],
          summary: {owned, total, paid}}

PATCH  /api/v1/collection-items/<pk>/
       {condition_type?, quantity?, price_paid?, acquisition_date?, location?, note?}
POST   /api/v1/collections/<pk>/items/  {stamp}
DELETE /api/v1/collection-items/<pk>/
```

Notes for the implementation:
- The list endpoints **must stop returning `all()`** (that is a data leak today,
  not a missing feature).
- Counts and sums with `annotate(Count(..., distinct=True), Sum(...))` over the
  `CollectionItem → Stamp → Issue` relation; the series page is one annotated
  query plus `count()`, same shape as `IssueService.get_issues`.
- `collection-items` PATCH must whitelist the six fields: `collection` and
  `stamp` are not editable, and the row must belong to a collection of the
  caller. **The API is the gate** (D2): whatever a normal user can change is
  exactly what these views allow, and nothing else in the catalogue is reachable
  with their token.
- Response serializers: reuse the existing ones where they fit
  (`StampResponseSerializer`, `IssueResponseSerializer`) and add a thin
  collection serializer; the cards need `market_value_mnh`/`used` and the colour
  names, which those serializers already carry.
- Pagination follows the house convention (`page`, `pageSize`, `sortBy`,
  `order`, and a `pagination` block), so `TablePagination` keeps working.

---

## 5. Frontend: files

```
services/collection_service.py           # Flet-free: list/get/create/rename/delete
services/collection_item_service.py      # Flet-free: series page, series detail,
                                         # patch item, add/remove copy
pages/collection/collections_page.py           # screen 1 (fills the skeleton)
pages/collection/collection_series_page.py     # screen 2
pages/collection/collection_issue_page.py      # screen 3
components/collection/collection_card.py
components/collection/issue_progress_card.py
components/collection/collection_stamp_card.py  # picture + catalogue + “Your copy”
components/form/dialogs/collection_form.py      # name; create and rename
components/form/dialogs/collection_item_form.py # optional: the six fields in a dialog
core/urls.py    # Backend + Frontend route constants
main.py         # the resolver described in §2
```

The services read the token from `SharedPreferences` (`USER_JWT_TOKEN`, saved by
`core/base_ui.py` at login together with the id, username, names and email) and
send it as `Authorization: JWT <token>`; the catalogue services keep using the
master key. Nothing new has to be stored.

### Frontend conventions this code has to follow

Read from the existing code, not invented; the first component of each kind copies
the closest one that already exists:

- **Pages** extend `StandardPage` (header + main + drawer), build the `AppHeader`
  in `__init__`, register in `main.py`'s route table, and take `page: ft.Page`.
- **Services** extend `BaseService`, stay **Flet-free**, are `async`, build the
  URL from `core.urls.URLs.Backend`, and return the raw
  `requests.Response` (or `None` on a network error) — the page decides what a
  status code means. `IssueService` is the reference, including its
  `_auth_headers` property.
- **Components** extend `ft.Container` (or `ft.View` for a page), receive their
  data as a `dict` plus callbacks (`on_edit`, `on_delete`) and never call a
  service themselves. `components/table/issue_detail/stamp_card.py` is the
  pattern for a card with a picture.
- **Dialogs** are the `ft.AlertDialog` builders under
  `components/form/dialogs/` (see `stamp_form.py`, `issue_form.py`).
- **Type hints and docstrings on every class and public method**, private methods
  with a leading underscore, constants in `UPPER_CASE`, colours imported from
  `components/colors.py`.
- **Money and dates**: `fmt_currency` and the same date formatting the admin uses;
  the picture path is resolved like `stamp_card.py` does (local
  `assets/stamps/<year>/<fesofi>.webp`, `no_stamp.webp` when missing).
- **Reuse before writing**: `YearRangeSelector`, `TablePagination`, `AppDrawer`,
  `TextField`, `AlertButton`/`DefaultButton`, `HEADER_HEIGHT` and
  `CARD_BORDER_RADIUS`.
- **Localization**: every user-visible string through `_("group.key")`; the JSON
  files under `assets/locales/` are user-managed and the agent never edits them.

**Tests** live in `frontend/tests/` with `pytest-asyncio` + `pytest-mock` and the
isolated `frontend/pytest.ini`. Each step brings its own: services are tested with
a mocked `_make_request` (URL, headers, payload and status handling), components
where Flet allows it (the `_values` descriptor problems are known and documented
in `progress.md`), and page-level behaviour that cannot be tested is checked by
hand and said so. The suite was at 651 passing tests before this feature.

**Locale keys needed** (the user supplies them in `en.json`/`es.json`): the
page titles and breadcrumbs, `New collection`, the rename/delete dialog and its
confirmation, `series`, `stamps`, `paid`, `catalogue`, the completion line
(`%(owned)s of %(total)s stamps`), the sort options, the empty states (no
collections, no series match, no stamps), the six field labels of “Your copy”,
`Edit`, `Save`, `Cancel`, `Remove from collection`, `Add my copy`, and the error
messages (load failed, save failed, delete failed).

---

## 6. Steps

| # | Step | Depends on | Size |
|---|---|---|---|
| 1 | **JWT + ownership**: `current_user(request)` from the token, the four collection views scoped to it (they return `all()` today), the new views added to `USER_VIEWS`, tests: no header → 403, bad token → 403, another user's row → 404 | — | S |
| 2 | Collections read: counters and cover in `GET /collections/`, `GET /collections/<pk>/`, tests | 1 | S |
| 3 | Series read: paginated `GET /collections/<pk>/issues/` with filters and order, tests | 2 | M |
| 4 | Series detail: `GET /collections/<pk>/issues/<issue_pk>/` with each stamp and `item` or `null`, tests | 3 | S |
| 5 | Item write: `PATCH` (whitelisted fields), `POST` (add copy), `DELETE` (remove copy) + tests | 4 | S |
| 6 | `CollectionService` + `CollectionItemService` (Flet-free) + unit tests with mocked responses | 1–5 | S |
| 7 | Screen 1: `CollectionsPage` with cards, empty state and the create/rename/delete dialog | 6 | M |
| 8 | Screen 2: `CollectionSeriesPage` with the paginated rows, search and year range, and the routes | 6, 7 | M |
| 9 | Screen 3: `CollectionIssuePage` with the series header and the stamp cards, “Your copy” save/remove | 6, 8 | L |
| 10 | Close-out: loading and error states, empty states, i18n pass, tests for the new components | 7–9 | S |

**Acceptance, per screen**
- Screen 1: a user with no collections sees the empty state and can create one;
  a card shows the counts and the bar matches them; clicking opens screen 2.
- Screen 2: 15 series per page with the totals in the footer; the browser back
  button returns to screen 1; a filter that matches nothing shows the empty
  state, not a broken pager.
- Screen 3: the series data cannot be edited (no control); the “Your copy” block
  saves and the card shows the new values without a reload; removing a copy asks
  once and the progress of the collection goes down.
- A user can never see another user's collection, series or item — a test per
  endpoint.

---

## 7. Out of scope (later phases)

- The **catalogue browser** with “select all stamps in a series” (the old plan's
  step 4). D2 only adds one copy at a time from the series screen.
- Adding pictures, sharing a collection, exporting it, CSV, stats over time.
- Editing the catalogue from here (that is DataDesk).
- The admin's Stamps Manager stays as it is; this is a new set of screens for
  non-admin users.

---

## 8. Risks

| Risk | When it shows | Plan B |
|---|---|---|
| A collection with 500 series makes the page slow | screen 2 | it is paginated from day one (D6); the query is one annotated queryset, never per row |
| N+1 on images | any card | resolved locally with `os.path.exists`, as the admin already does; a missing picture falls back to `no_stamp.webp` |
| The API keeps leaking other users' rows | while implementing | step 1 is exactly that fix, with tests, before any screen is built. With the master key the leak remains (that key is allowed everywhere by design), so the app must send the **JWT** on these screens |
| The token expires (24 h) in the middle of a session | any screen | the API answers 403; the services treat it as "session expired" and send the user to the login, as `main.py` already does when `validate_jwt_token` fails |
| Flet `_values` descriptor issues on views | tests of pages | the same deferral the admin pages have: test the services and the components, not `ft.View` internals |
| Locale keys missing | every screen | the key list in §5 is handed over before step 7; while they are missing, the screens show the key (as the app does today) |
| Money and dates formatted differently from the admin | screens 2 and 3 | reuse `fmt_currency` and the same currency symbols the admin shows |

---

## 9. State when this was parked (2026-11-23)

Nothing implemented. The plan, the decisions (§3) and the three mockups are the whole
deliverable so far.

**Next action: step 1 of §6**, announced to the user and waiting for the go-ahead:

1. `backend/common/core/current_user.py` (new): `current_user(request)` reads
   `Authorization: JWT <token>`, validates it with `JwtToken().validate()` and returns
   the `UserCollection`; a missing header, a bad token or an unknown user raise
   `PermissionDenied` (403, the response `HasSpecificKeyName` already gives).
2. The four collection views filter by that user instead of `all()`, and answer 404 for
   another user's object; `POST /collections/` stops taking the user from
   `X-API-KEY` (the `# TODO` in `collections_view.py`) and uses the helper.
3. `USER_VIEWS` already lists the four views; the new ones join in steps 3 and 4.
4. Tests in `collections_api/test/` and `collection_items_api/test/` (with
   `AbstractApiUnitTest`): the current ones assert "all collections" and change; new
   cases for only mine, another user's pk → 404, no header → 403, bad token → 403.

**Two questions left for the user before writing that code**

- Does the `collection-items` `PATCH` whitelist (only the six “Your copy” fields) close
  in step 1 or in step 5, where it belongs by the plan?
- Do the existing collection tests move from `permission(granted=True)` to a real
  `Authorization: JWT` header (more work now, but the test base then points at the real
  mechanism)?

No frontend work has started: no service, no page, no component, no locale key.

