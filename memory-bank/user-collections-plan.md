# Normal-user collections: the reading screens

> **Status**: revised 2026-11-26, **implementation not started** — next is step A1 (§6)
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
  `components/table/column_def.py` (not `core/utils.py`), `_()` from
  `core/translations.py`, and the stamp pictures:
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
- Endpoints: `GET /api/v1/collections/` (and `/<pk>`, create, update, delete),
  `GET /api/v1/collection_items/` (and `/<pk>`, create, update, delete).
  **What is wrong with them**:
  1. they return `Collection.objects.all()` / `CollectionItem.objects.all()` —
     every user's data, with no ownership check at all; and a `POST` of an item
     accepts any `collection` id, so it can write into somebody else's collection;
  2. `?username=` is declared in the schema of `CollectionsView` and then
     ignored — and it is not the way in either: the token says who is asking
     (D0);
  3. creating a collection relies on `X-API-KEY` being the user's
     `password_hash` (`# TODO. This need to be fixed`);
  4. no counts, no pagination, no "the series of a collection" and no
     "the stamps of one series with my copy".
- Authentication: the public API uses `CustomAPIKeyAuthentication` +
  `HasSpecificKeyName`, i.e. **one master key** shared by the app
  (`API_MASTER_KEY` in the Flet settings). The JWT that the login issues is accepted
  only on the views listed in `USER_VIEWS` (the four collection ones are), but those
  views ignore who the token belongs to and return every user's rows.
  `common/core/jwt_token.py` already validates it and returns `user_id`, and
  `users_api.UserToken` exists.
- `Collection.user` is nullable, so rows created before this feature may have no
  owner. After scoping they are invisible to everybody; if any exist in production
  they are fixed from DataDesk, not here.
- The locale system has **no plurals** (`_()` has no `_one`/`_other`), so any sentence
  with a count is written with neutral labels (`Series: 3 · Stamps: 9`), never
  `1 series · 1 stamps`.
- Data volume: 2.540 series, 9.555 stamps, 88% with a picture.

---

## 2. The three screens

1. **Collections** — `/collections`. A card per collection: collage of up to six
   stamps, name, `Series: N · Stamps: M` and a completion bar (stamps owned / stamps
   in those series). `+ New collection` and the empty state. No pagination: they are
   one person's collections. The cards are **not clickable until B3**, when the route
   of the second screen exists: a step does not leave a dead door. The app bar carries
   the menu and the page title only: the user already lives in the drawer, so no name
   on the right and no separator for it (revised 2026-11-26, mockup updated).
2. **One collection** — `/collections/<id>`. Its series, **paginated server-side
   with the same contract as `/issues/`** (15 per page, `sortBy=date` by default,
   ties broken by `id`): thumbnail, `year · date`, name, country and stamp type,
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

All closed; the plan was revised on 2026-11-26 with the corrections found against the
code (the real status for a missing header, item ownership, the `/issues/` order,
Flet-free services) and is ready
to implement step by step (§6).

| # | Decision | Closed |
|---|---|---|
| D0 | **How the API knows the user.** | **Closed 2026-11-22: the JWT the login returns.** The collection requests send `Authorization: JWT <token>` (`USER_JWT_TOKEN`, stored by `core/base_ui.py` at login), which is what `HasSpecificKeyName` already understands: its `JWT` branch validates the token and the view must be listed in `USER_VIEWS` (the four collection views already are). A missing header answers **403** — measured in A1: DRF turns `AuthenticationFailed` into 401 only when the authentication class declares a challenge header, and `CustomAPIKeyAuthentication` does not, so it falls back to 403. A bad or expired token, or the master key used on these views, also answers **403**; making a missing header a true 401 is a global change (a `WWW-Authenticate` header plus 75 test expectations) and is not part of this feature. The user is taken from the token itself: `JwtToken.validate()` returns `user_id`, `username`, names and email, so **no `?username=` is needed** and no query parameter can lie about who is asking. The catalogue endpoints keep the master key. |
| D1 | **Can the user create / rename / delete a collection?** | **Closed 2026-11-22: yes.** A `CollectionForm` dialog with the name only, for create and rename, and a delete that warns with the counts of what goes with it (series and stamps of *their* rows; the catalogue is untouched). Without it a new user could never fill the page. |
| D2 | **Can the user add a stamp to a collection, or remove their copy?** | **Closed 2026-11-22: yes, and only their copy.** `Add my copy` creates a `CollectionItem`; `Remove from collection` deletes it. The catalogue (series and stamps) is **admin-only**: a normal user's token is accepted only on the views listed in `USER_VIEWS`, which is why these screens send the JWT and the admin screens keep the master key. The catalogue browser with “select all stamps in a series” stays a later phase. |
| D3 | **Which “Your copy” fields are editable?** | All six. `condition_type` and `location` are **selects** from their tables (read-only lists for the user); `quantity` ≥ 1; `price_paid` with two decimals; `acquisition_date` with the existing `DatePickerField`; `note` multiline. |
| D4 | **What does a collection card show?** | **Closed 2026-11-23: a collage of up to six stamps**, plus the name, the summary (`Series: N · Stamps: M`) and the completion bar. The six are **stable**, not random on every load (a card that shuffles is a card you stop recognising): the API sends up to **12** of the collection's stamps in a stable order and the frontend paints the first **six whose file exists** — the picture lives in the frontend's tree, so only it knows. A collection with no stamps (or with none of its pictures) shows `no_stamp.webp`, greyed like the admin does. Layout: one stamp centred and big, two to six as a mosaic of three columns; no empty holes. The covers of a whole page come in **one** query, not one per card. |
| D5 | **What does a series card show?** | **Closed 2026-11-23:** thumbnail, `year · date`, name, country and stamp type, `3 of 5 stamps · 60%` with the bar, **paid** (sum of `price_paid` of the user's items) and **catalogue (MNH)** (sum of the series' stamps). Two figures because they answer two questions: what it cost me and what the catalogue says it is worth. To be refined later with real data. |
| D6 | **Pagination** | Server-side, **15 series per page** by default (same as the admin table), selector 15/30/50. Reuses `TablePagination`, which gains two optional parameters — `page_size_options` (defaults to today's list) and `label` (defaults to the current key) — so its other screens do not change. Never load a whole collection. |
| D7 | **Default order of the series** | **Revised 2026-11-26: the one `/issues/` already uses.** `sortBy=date` and `order=asc` by default, ties broken by `id`, which makes the order total and keeps OFFSET paging from repeating a row. Selector `Date ↑`, `Date ↓`, `Name`. No catalogue-code tiebreak and nothing from DataDesk: the collections API mirrors the issues endpoint. |
| D8 | **Do stamps I don't own appear in the series?** | **Closed 2026-11-23: yes, dimmed**, with `Add my copy`. The progress bar needs its denominator and “what is missing” is half the reason to open a collection. |
| D9 | **Search and filters inside a collection** | Name search plus year range in the first version (both cheap server-side); country/stamp type later. |
| D10 | **Money on screen** | `fmt_currency` from `components/table/column_def.py` (already used by the admin), Spanish grouping (`37.500,00 €`), from the raw decimals the API sends. |

---

## 4. Backend: what is missing

Everything lives under `/api/v1/`, with **`Authorization: JWT <token>`** (D0), scoped to
the user the token carries. A missing header answers **403**: DRF's authentication
class raises `AuthenticationFailed`, but DRF only turns that into 401 when the class
declares a challenge header, and `CustomAPIKeyAuthentication` does not — so it falls back
to 403. A bad or expired token, or the master key used on these views, is also a **403**. A
collection or item of another user answers **404**, never 403: whether it exists is none of
the caller's business.

The envelope and the pagination are the ones `/issues/` already uses: `page`,
`pageSize`, `sortBy`, `order` and a `pagination` block with `sort_by`, `order`, `page`,
`page_size`, `total`, `has_more`. The series list **mirrors `/issues/` on purpose** — same
parameters, same defaults (`sortBy=date`, `order=asc`, ties broken by `id`) — so
`TablePagination` and the existing parsing work unchanged. It is a new endpoint because
`/issues/` knows nothing about collections and would return the whole catalogue.

`common/core/current_user.py` (new) is the first thing to write: the **class**
`CurrentUser`, used as `CurrentUser(request).get()`. It reads `Authorization`, requires
the `JWT` scheme, validates with `JwtToken().validate()` and returns the `UserCollection`;
a missing header, a bad token, an unknown `jti` or an unknown user raise
`PermissionDenied`. The views use it instead of `all()`. It validates a second time on
purpose (the permission already did) so a view never depends on a side effect of another
class.

```
GET    /api/v1/collections/
       -> [{id, name, series, stamps, total, covers:[{year, code} up to 12]}]

GET    /api/v1/collections/<pk>/
POST   /api/v1/collections/            {name}
PUT    /api/v1/collections/<pk>/       {name}
DELETE /api/v1/collections/<pk>/       (the items go with it, by cascade)

GET    /api/v1/collections/<pk>/issues/?page=&pageSize=&name=&year=&sortBy=&order=
       -> {issues: [{id, year, date, name, country, stamp_type, cover,
                     total_stamps, owned_stamps, paid, catalogue_mnh}],
           pagination: {sort_by, order, page, page_size, total, has_more}}

GET    /api/v1/collections/<pk>/issues/<issue_pk>/
       -> {issue: {the 15 catalogue fields},
           stamps: [{stamp..., item: {id, condition_type, quantity, price_paid,
                                      acquisition_date, location, note} | null}],
           summary: {owned, total, paid}}

POST   /api/v1/collections/<pk>/items/  {stamp}
PUT    /api/v1/collection_items/<pk>/   {condition_type, quantity, price_paid,
                                         acquisition_date, location, note}
DELETE /api/v1/collection_items/<pk>/
```

Notes for the implementation:

- **The list endpoints stop returning `all()`** — collections **and** items. That is a
  data leak today, not a missing feature. `POST /collection_items/` must reject a
  `collection` that is not the caller's, and the item update (`PUT`) must accept only the
  six "Your copy" fields: without that, an item can be moved into someone else's
  collection.
- Overview counters: `series` = distinct issues among the user's items; `stamps` =
  distinct stamps owned (a `quantity` of 2 does not inflate the card); `total` = stamps
  of **those** issues (the bar's denominator: what is missing from what was started);
  `covers` = up to 12 `{year, code}` from the user's stamps that carry a `fesofi_code`,
  in a stable order. Empty collection -> `0, 0, 0, []`. At most five queries for the
  whole page, independent of the number of cards.
- Series and detail read the catalogue (series and stamps) and attach **only the
  caller's** `item`. Counts and sums with `annotate(Count(..., distinct=True), Sum(...))`
  over the items; the series page is one annotated query plus `count()`, never one per
  row.
- **DataDesk is not part of this feature**: no import, no shared helper, no ordering
  function from it. The collections API is its own reader and mirrors `/issues/`.
- New views (`CollectionIssuesView`, `CollectionIssueDetailView`,
  `CollectionIssueItemsView`) join `USER_VIEWS`; the four existing ones are already
  there.
- Response serializers: reuse `IssueResponseSerializer` and `StampResponseSerializer`
  where they fit, and add thin ones for the cards (`CollectionOverviewSerializer`,
  `CollectionIssueSummarySerializer`). The single-collection response keeps its shape
  (`id`, `user`, `name`); the overview uses its own and does not nest the user.

---

## 5. Frontend: files

```
services/collection_service.py                    # Flet-free: list/create/rename/delete
services/collection_item_service.py               # Flet-free: series, detail, item writes
pages/collection/collections_page.py              # screen 1 (fills the skeleton)
pages/collection/collection_series_page.py        # screen 2
pages/collection/collection_issue_page.py         # screen 3
components/collection/collection_card.py
components/collection/issue_progress_card.py
components/collection/collection_stamp_card.py    # picture + catalogue + "Your copy"
components/form/dialogs/collection_form.py        # name; create, rename and delete confirm
core/urls.py    # Backend + Frontend route constants
main.py         # the resolver described in §2
```

The backend helper `common/core/current_user.py` is described in §4 and belongs to A1.

The **services are Flet-free and receive the token** (`CollectionService(token)`), exactly
like `IssueService` receives the master key from `settings`. The token is read from
`SharedPreferences` by the **page** (`USER_JWT_TOKEN`, saved by `core/base_ui.py` at
login) and handed to the service; a service that read prefs would drag Flet into the
layer that has to be testable without it. The catalogue services keep the master key.

### Frontend conventions this code has to follow

Read from the existing code, not invented; the first component of each kind copies the
closest one that already exists:

- **Pages** extend `StandardPage` (header + main + drawer), build the `AppHeader` in
  `__init__`, register in `main.py`'s route table, and take `page: ft.Page`. The
  collections pages do **not** add the `VerticalLine` separator behind the title: the
  revised mockup has no user on the right, so there is nothing to separate.
- **Services** extend `BaseService`, stay **Flet-free**, are `async`, build the URL from
  `core.urls.URLs.Backend`, and return the raw `requests.Response` (or `None` on a
  network error) — the page decides what a status code means. `IssueService` is the
  reference, including its `_auth_headers` property.
- **Components** extend `ft.Container` (or `ft.View` for a page), receive their data as a
  `dict` plus callbacks (`on_open`, `on_edit`, `on_delete`) and never call a service
  themselves. `components/table/issue_detail/stamp_card.py` is the pattern for a card
  with a picture.
- **Dialogs** are the `ft.AlertDialog` builders under `components/form/dialogs/`, shown
  on `page.overlay` (see `stamp_form.py`).
- **Type hints and docstrings on every class and public method**, private methods with a
  leading underscore, constants in `UPPER_CASE`, colours imported from
  `components/colors.py` (no raw hex).
- **Money and dates**: `fmt_currency`, `fmt_number` and `fmt_date` from
  `components/table/column_def.py`; the picture path is resolved like `stamp_card.py`
  does (local `assets/stamps/<year>/<fesofi>.webp`, `no_stamp.webp` when missing).
- **Reuse before writing**: `YearRangeSelector`, `TablePagination`, `AppDrawer`,
  `TextField`, `AlertButton`/`DefaultButton`/`PrimaryButton`, `HEADER_HEIGHT` and
  `CARD_BORDER_RADIUS` from `components/constants.py`.
- **Localization**: every user-visible string through `_("group.key")`; the JSON files
  under `assets/locales/` are user-managed and the agent never edits them. Counts are
  written with neutral labels because the translation helper has no plurals.

**Tests** live in `frontend/tests/` with `pytest-asyncio` + `pytest-mock` and the isolated
`frontend/pytest.ini`. Services are tested with a mocked `_make_request` (URL, headers,
payload and status handling), components where Flet allows it (the `_values` descriptor
problems are known and documented in `progress.md`), and page-level behaviour that cannot
be tested is checked by hand and said so. The suite was at 651 passing tests before this
feature.

**Locale keys for phase A** (the user supplies them in `en.json`/`es.json`, with
placeholders so each language decides the wording):

```
collections.title            (exists)
collections.your_collections
collections.count            "Collections: {count}"
collections.summary          "Series: {series} · Stamps: {stamps}"
collections.new
collections.empty_title
collections.empty_hint
collections.new_title
collections.rename_title
collections.rename
collections.name_label
collections.create
collections.save
collections.cancel
collections.delete_title
collections.delete_message
collections.delete_confirm
collections.name_required
collections.session_expired
collections.load_failed
collections.save_failed
collections.delete_failed
```

Phase B adds its own list (progress line, sort options, filters, the six "Your copy"
labels, `Add my copy`, `Remove from collection`) and hands it over before B3.

---

## 6. Steps

Two phases. **Phase A** ships the overview end to end and leaves a usable screen.
**Phase B** starts only when A is closed, committed and merged into `development`, and
adds the other two screens. Every step leaves the app running.

### Phase A — Collections overview

| # | Step | Depends on | Size | Status |
|---|---|---|---|---|
| A1 | Ownership and JWT | — | M | **hecho 2026-11-26** |
| A2 | Overview list: counters and covers | A1 | S | **hecho 2026-11-26** |
| A3 | `CollectionService` | A2 | S | **hecho 2026-11-26** (mergeado, PR #477) |
| A4 | `CollectionCard` | A3 | M | **hecho 2026-11-26** |
| A5 | Screen, dialog and states | A4 | M | **hecho 2026-11-26** |
| A6 | Phase A close-out | A5 | S | **hecho 2026-11-26** |

**A1 — Ownership and JWT (backend) — HECHO 2026-11-26.**
The `CurrentUser` class (`common/core/current_user.py`); the four collection and item views scoped to the token's
user; the item update serializer (`PUT`) reduced to the six fields; `POST
/collection_items/` refuses a foreign `collection`; `POST /collections/` stops taking the
user from `X-API-KEY`; the `?username=` parameter and its `# TODO` are removed. Tests:
only mine, a foreign pk answers 404 in GET, PUT and DELETE, `POST` creates for the token's
user and ignores a `user` in the body, no header 403, bad token 403, master key 403, plus
unit tests for `CurrentUser`. The old tests that assert "all collections" are rewritten with a real
JWT (`JwtToken().create()` in a fixture) — there is no way around it once the views read
the token.
*Leaves working:* the API no longer leaks between users and the suite proves it. No UI.
*Done:* 51 tests with real tokens (the suites plus the shared `Authorization`
parser), the whole suite at 1.767, and a measured correction — a missing header is 403,
not 401 (see §9).

**A2 — Overview list (backend) — HECHO 2026-11-26.**
`CollectionOverviewSerializer` and the counting function behind `GET /collections/`:
`series`, `stamps`, `total` and up to 12 `covers`, in at most five queries. Ordered by
name, no pagination. Tests: two users, a `quantity` of 2, a cover without `fesofi_code`,
an empty collection, the query count.
*Leaves working:* `curl` returns the cards complete.
*Done:* `CollectionOverviewService` (five queries, pinned by a test) and
`CollectionOverviewSerializer`; `series`, `stamps` and `total` are three different
numbers in the test data; the covers keep only stamps with a `fesofi_code`, are stable
and are capped at 12. 14 tests new, suite at 1.781.

**A3 — `CollectionService` (frontend) — HECHO 2026-11-26 (mergeado, PR #477).**
`services/collection_service.py` with `get_collections`, `create_collection`,
`update_collection` (PUT) and `delete_collection`; `URLs.Backend.collections` and
`collection_items`; the service takes the token and sends `Authorization: JWT`. Tests
with a mocked `_make_request`: URL, header, payload, status handling, `None` on network
error.
*Leaves working:* the service is testable and the page can call it.
*Done:* `CollectionService` with the token in the constructor and the four calls;
`URLs.Backend.collections` and `collection_items`; 9 tests with `_make_request`
mocked, and the frontend suite at 660.

**A4 — `CollectionCard` — HECHO 2026-11-26.**
`components/collection/collection_card.py`: collage of up to six stamps (one big,
2–6 in three columns, `no_stamp.webp` when none), name, summary, bar and percentage.
It takes no click handler yet: B3 adds it when the route exists. Tests: 0/1/6 covers,
missing file, `total = 0`.
*Leaves working:* the card renders on its own, with any data dict.
*Done:* `CollectionCard` paints the first six covers whose file exists (one big, or a
three-column mosaic), the placeholder when none does, the summary through
`collections.summary`, and the bar with its percentage (`—` when the collection is
empty). It is not clickable until B3. `fmt_number` gained a `zero` argument so a counter
that is zero reads `0` while the tables keep their dash. 14 tests; frontend suite 675.

**A5 — Screen, dialog and states — HECHO 2026-11-26.**
`CollectionsPage`: header without separator, toolbar with the count and
`+ New collection`, responsive grid, empty state, loading and error. `read_prefs` reads
the JWT and builds the service; 403 sends the user to the login. `collection_form.py`:
create/rename dialog and the delete confirmation with the card's counts. Tests for the
static helpers; the page itself, by hand.
*Leaves working:* phase A is usable end to end.
*Done:* `CollectionsPage` with the header without separator, the toolbar (title, count and
`+ New collection`), the responsive grid, the empty/loading/error states and the 403 →
login path; `CollectionForm` and `CollectionDeleteDialog`; the card gained a menu with
rename and delete, shown only when the page passes the handlers. `PAGE_PADDING` joined the
constants. The name field is created with `expand=False`: a text field expands by
default, and inside the dialog's column that stretched the dialog to the full height of
the window — found on first use, pinned by a test. 23 tests (dialogs, construction and
render on a mocked page); frontend suite **698**, checked by hand for the paths a page
cannot test.

**A6 — Phase A close-out — HECHO 2026-11-26. Phase A is closed.**
Two real users in the browser; empty state, create, rename, delete, reload and expired
token. Suite green. `progress.md`, `activeContext.md` and this plan updated.

### Phase B — One collection, one series

| # | Step | Depends on | Size | Status |
|---|---|---|---|---|
| B1 | Series of a collection (backend) | A6 | M | **hecho 2026-11-26** |
| B2 | Series detail and item writes (backend) | B1 | M | **hecho 2026-11-26** |
| B3 | `CollectionSeriesPage` | B2 | L | **hecho 2026-11-26** |
| B4 | `CollectionIssuePage` | B3 | L | pendiente |
| B5 | Close-out | B4 | S | pendiente |

**B1 — Series of a collection — HECHO 2026-11-26.**
`GET /collections/<pk>/issues/` mirroring `/issues/`: same parameters, same defaults,
same `pagination` block, plus `cover`, `total_stamps`, `owned_stamps`, `paid` and
`catalogue_mnh`. One annotated query plus `count()`. `CollectionIssuesView` joins
`USER_VIEWS`. Tests: pagination, filters, order with repeated dates, sums, foreign
collection 404, query count.

**B2 — Series detail and item writes — HECHO 2026-11-26.**
`GET /collections/<pk>/issues/<issue_pk>/` with every stamp and its `item` or `null`, and
the `summary`; `POST /collections/<pk>/items/` (409 when the stamp is already there);
`PUT`/`DELETE` already scoped from A1, now answering with the names of condition and
location. Tests: unowned stamp has `item: null`, adding, duplicate 409, removing,
foreign 404.

*Done:* `CollectionIssueDetailService` (the issue, its stamps, their colours and the
caller's items: **four** queries, not three — the colours are a prefetch) and
`CollectionIssueDetailSerializer`, which reuses `StampResponseSerializer` and adds
`item` flat. `POST /collections/<pk>/items/` answers 201, 404 for a foreign collection or
an unknown stamp, and 409 for a duplicate without touching the existing copy. 16 tests;
suite **1.818**. The figures serializer was renamed `CollectionIssueFiguresSerializer`:
two components called `CollectionIssueSummary` made drf-spectacular warn.

**B3 — `CollectionSeriesPage` — HECHO 2026-11-26.**
`main.py` grows the parameter resolver; the overview card becomes clickable. The page
reuses `TablePagination` with `page_size_options=[15, 30, 50]` and its own `label`, the
name search with debounce and `YearRangeSelector`. `Services` gain `get_collection` and
`get_series`. Tests: service params, row formatting, paginator defaults.

*Done:* `RouteResolver` (`core/routing.py`) resolves `/collections/<id>` and leaves the
exact table alone; `CollectionCard` is clickable when it receives `on_open`, and the
overview passes it. `CollectionSeriesPage` with the breadcrumb, the name and the two
counters from the overview row, the name/range/sort filters and the shared paginator
with 15/30/50 and its own label. `IssueProgressCard` paints the row. **The header shows
series and stamps, not the collection's paid total**: the overview row does not carry it,
and adding it would be a backend change; the per-series paid is in each row. 37 tests
more; frontend suite **744**. No browser pass: the running backend image predates B1/B2,
so the rows cannot load until it is rebuilt.

**B4 — `CollectionIssuePage`.**
Read-only series header (`hide_action_icons=True`) with the catalogue badge, then one
`CollectionStampCard` per stamp: picture, codes, face value, colours, catalogue values,
and "Your copy" with the six fields, save/cancel/remove and `Add my copy` for the ones
the user does not own. Refreshes the summary without a reload. Tests: service writes,
card in read and edit mode, stamp without an item.

**B5 — Close-out.**
Loading, error and empty states on both screens, the i18n pass with the phase B keys,
`TablePagination` covered, and a browser pass with an empty collection, a full one and a
series with no stamps.

**Acceptance, per screen**

- Screen 1 (A5): a user with no collections sees the empty state and can create one; a
  card shows the collage, the summary and a bar that matches the counters; rename and
  delete work and the page reloads with the change; the API never returns another user's
  collection.
- Screen 2 (B3): 15 series per page with the totals in the footer; the browser back
  button returns to screen 1; a filter that matches nothing shows the empty state, not a
  broken pager; the order matches what `/issues/` would return.
- Screen 3 (B4): the catalogue data cannot be edited (no control); "Your copy" saves and
  the card shows the new values without a reload; removing a copy asks once and the
  progress of the collection goes down.
- A user can never see or write another user's collection, series or item — a test per
  endpoint.

## 7. Out of scope (later phases)

- The **catalogue browser** with “select all stamps in a series” (the old plan's
  step 4). D2 only adds one copy at a time from the series screen.
- Adding pictures, sharing a collection, exporting it, CSV, stats over time.
- Editing the catalogue from here: the catalogue is admin-only, and these screens only
  read it.
- The admin's Stamps Manager stays as it is; this is a new set of screens for
  non-admin users.

---

## 8. Risks

| Risk | When it shows | Plan B |
|---|---|---|
| A collection with 500 series makes the page slow | screen 2 | paginated from day one; one annotated queryset plus `count()`, never per row |
| N+1 on images | any card | resolved locally with `os.path.exists`, as the admin already does; a missing picture falls back to `no_stamp.webp` |
| The API keeps leaking other users' rows | while implementing | A1 is exactly that fix, with tests, before any screen is built. The master key is allowed everywhere by design, so the app sends the **JWT** on these screens and `CurrentUser` refuses the master key there |
| The token expires (24 h) in the middle of a session | any screen | the API answers 403; the page treats it as "session expired" and sends the user to the login, as `main.py` already does when `validate_jwt_token` fails |
| Logging in again invalidates the previous token (`UserToken` is one per user) | manual testing with two windows | expected; the second window gets 403 and the login. Not a bug to fix here |
| Flet `_values` descriptor issues on views | tests of pages | the same deferral the admin pages have: test the services and the components, not `ft.View` internals |
| Locale keys missing | every screen | the key lists are handed over before A5 and B3; while they are missing the screens show the key (as the app does today) |
| Counts with plurals ("1 series") | any label | neutral labels (`Series: 1 · Stamps: 1`), because the locale helper has no plural forms |
| Money and dates formatted differently from the admin | screens 2 and 3 | reuse `fmt_currency` / `fmt_date` from `components/table/column_def.py` |

---

## 9. State when this was revised (2026-11-26)

Nothing implemented: no helper, no endpoint, no service, no page, no key. The plan, the
decisions (§3) and the three mockups are the whole deliverable so far.

**Decisions closed while revising it**

1. The user comes from the **JWT**. Measured in A1: a missing header, a bad token and
   the master key all answer **403** (DRF only makes it 401 with a challenge header, and
   `CustomAPIKeyAuthentication` has none), and a foreign row answers **404**.
2. **A1 includes the item views and the update whitelist (`PUT`)**, not just the collection
   views: otherwise an item can be moved into someone else's collection.
3. The series order **mirrors `/issues/`** (`sortBy=date`, ties by `id`). No catalogue
   code and **nothing from DataDesk**.
4. Rename uses the existing **`PUT /collections/<pk>/`**; no `PATCH` was added.
5. Overview counters: `stamps` = distinct stamps owned; `total` = stamps of the series
   the user has something in; `quantity` does not inflate the card.
6. Counts are written with **neutral labels**, because the locale system has no plurals.
7. The frontend reaches the database **only through the API**. DataDesk is out of the
   equation.

**A1 is done (2026-11-26).** The `CurrentUser` class exists and the four
collection and item views are scoped with `CurrentUser(request).get()`; the item update has its own six-field
serializer and refuses `collection` and `stamp`; `POST /collection_items/` refuses a
collection that is not the caller's; `POST /collections/` takes the owner from the token
(the `X-API-KEY` lookup and the `# TODO` are gone) and `?username=` is out of the schema.
51 tests across `test_authorization.py`, `test_current_user.py`, `test_collections_api.py`
and `test_collection_items_api.py`, with real tokens; the suite is at **1.767** because the
old auth permutations (the same `PermissionDenied` mocked on every method) were replaced
by one case per behaviour, already covered centrally in `common/test/test_permissions.py`.

**Shared with the permission**: `common/core/authorization.py` holds the only parser of the
`Authorization` header; `HasSpecificKeyName` and `CurrentUser` both use it instead of each
splitting the string.

**Measured while implementing**: a missing header is **403**, not 401 — DRF only converts
`AuthenticationFailed` into 401 when the authentication class declares a challenge header,
and `CustomAPIKeyAuthentication` does not. The plan, this section and the issue
description said 401; the code is what the framework does. A true 401 would need
`authenticate_header()` and 75 test expectations across the suite, so it is left out of
this feature.

**A2 is done (2026-11-26).** `GET /collections/` returns the caller's collections with
`series`, `stamps`, `total` and up to 12 covers, in exactly **five queries** (pinned by
`django_assert_num_queries`). The fixture makes the three figures different on purpose
(two stamps owned across two series, four in those series), a `quantity` of 2 still
counts as one stamp, a stamp without a `fesofi_code` is not a cover, and a collection
without an owner is not listed. 14 tests new; suite **1.781**.

**A3 is done and merged (2026-11-26, PR #477).** `CollectionService(token)` sends
`Authorization: JWT` and offers the four calls; the URLs live in `URLs.Backend`; 9 tests
mock `_make_request` and assert URL, method, header and payload, plus the `None` on a
network error.

**A4 is implemented (2026-11-26) and not merged yet.** It lives in the branch
`478-feature-collections-overview-card`, uncommitted: `components/collection/collection_card.py`
and its 14 tests, plus the `zero` argument of `fmt_number`. Frontend suite **675**.

**A5 is done (2026-11-26).** The overview is a usable screen: grid, empty/loading/error,
create/rename/delete and the 403 → login path.

**A6 is done (2026-11-26) and phase A is closed.** The browser pass covered the list,
create, delete, rename and the expired-token path; the locale files are complete and
equal; suites at **1.781** backend / **707** frontend. Two things could not be checked
headlessly and are named above: the painted covers (the renderer here does not paint
Flutter images) and the empty state (no account without collections on hand).

**B1 is done (2026-11-26).** `GET /collections/<pk>/issues/` returns the page with the
three figures and the cover in two queries; 21 tests, suite **1.802**.

**B2 is done (2026-11-26).** The detail with every stamp and its copy, and adding one
(201/404/409), are in; 16 tests, suite **1.818**.

**B3 is done (2026-11-26).** The second screen, the resolver and the clickable cards;
frontend suite **744**. Next action: **B4** — the series detail and "Your copy".
