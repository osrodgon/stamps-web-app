# Normal User Stamp Collections Management Plan

> **Status**: Planned / Ready for Implementation  
> **Target Audience**: Normal (authenticated) users  
> **Key Goal**: Provide user-owned stamp collections management, hierarchical card views, catalog search with year/issue filtering, and batch stamp selection ("Select All in Series").

---

## 🎨 UI Design Mockups & References

Mockup images are stored in `/workspaces/stamps-web-app/memory-bank/mockups/`.

### 1. Collections Overview Page
- Displays cards for all user-owned stamp collections with completion progress bars.
- Top-right `+ Add Collection` primary action button.
- Edit / Delete actions per collection card.

![Collections Overview](/workspaces/stamps-web-app/memory-bank/mockups/collections_overview_mockup_1787932573235.png)

### 2. Collection Detail View
- Displays collection items grouped hierarchically by Issue series.
- Hierarchical structure: `Collection` $\rightarrow$ `Issues in Collection` $\rightarrow$ `Stamps in Issues`.
- Completion percentage per issue (e.g. `4 / 5 Stamps (80%)`).
- Missing stamps rendered semi-transparent with a quick `+ Add` button.

![Collection Detail View](/workspaces/stamps-web-app/memory-bank/mockups/collection_detail_view_mockup_1787932584771.png)

### 3. Stamp Catalog Browser & Add Modal
- Year Range dual-slider filter (`1850 - 1900`), text search field, and dropdown filters.
- **"Select All Stamps in Series"** batch selection button next to each issue header.
- Individual check controls on stamp card thumbnails.

![Stamp Catalog Browser](/workspaces/stamps-web-app/memory-bank/mockups/stamp_catalog_picker_mockup_1787932601346.png)

---

## 🏗️ Architecture & Component Roadmap

```
frontend/
├── pages/
│   └── collection/
│       ├── collections_page.py           # Main entry view for user collections grid
│       └── collection_detail_page.py     # Detailed hierarchical view of a collection
├── components/
│   ├── collection/
│   │   ├── collection_card.py            # Card representation of a single collection
│   │   ├── collection_issue_card.py      # Card for issues in a collection (with progress)
│   │   └── stamp_catalog_picker.py       # Catalog browser with "Select All in Series"
│   └── form/
│       └── dialogs/
│           └── collection_form.py        # Create/Edit collection dialog (Collection name)
└── services/
    ├── collection_service.py             # Calls /api/collections/ endpoints
    └── collection_item_service.py        # Calls /api/collection-items/ endpoints
```

---

## 📋 Step-by-Step Execution Plan

### Step 1: `CollectionService` & Collection CRUD Dialog
- Implement `frontend/services/collection_service.py` to communicate with `/api/collections/`.
- Build `CollectionForm` dialog (`Collection name` field with underline styling).
- Wire `CollectionsPage` with `CollectionService.get_collections()`.

### Step 2: `CollectionsPage` Grid & Card Controls
- Build `CollectionCard` component with progress bar, updated timestamp, and edit/delete triggers.
- Implement empty state when user has no collections.

### Step 3: `CollectionDetailPage` & Hierarchical Issue Cards
- Build `CollectionIssueCard` component for hierarchical grouping (`Collection` $\rightarrow$ `Issue` $\rightarrow$ `Stamps`).
- Show collected vs missing stamp visual states (green checkmark vs semi-transparent thumbnail).

### Step 4: `StampCatalogPicker` & Batch "Select All in Series"
- Build catalog browser with `YearRangeSelector`, issue name filter, and country/type dropdowns.
- Add **"Select All Stamps in Series"** toggle to select/deselect all stamps belonging to an issue in one click.
- Wire batch POST to `/api/collection-items/` to save items to collection.

### Step 5: Unit Tests
- Create tests in `frontend/tests/test_collection_service.py`, `frontend/tests/test_collection_form.py`, and `frontend/tests/test_stamp_catalog_picker.py`.
