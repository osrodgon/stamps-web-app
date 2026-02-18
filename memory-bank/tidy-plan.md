# Tidy Plan - Stamps Manager Page Refactoring

## Completed
- ✅ Extract AI Series Lookup Drawer to component (`components/stamps/ai_series_lookup.py`)

---

## Priority 1: Extract Stamp Filters Component

**Location:** `_setup_filters()` + `get_years()` + `enable_years_slider()`

Currently the filter logic is split across 3 methods and tightly coupled:
- `_setup_filters()` - creates series input + tooltip
- `get_years()` - dynamically creates years slider 
- `enable_years_slider()` - toggles slider state

### Proposed Component: `components/stamps/stamp_filters.py`

```python
class StampFilters(ui.row, BaseUI):
    """
    Filter controls for stamp issues: series name input + years range slider.
    """
    
    def __init__(self, on_filter_change: callable):
        """
        Args:
            on_filter_change: Callback when filter values change
        """
```

**Lines saved:** ~80 lines

---

## Priority 2: Move Styles to CSS File

**Location:** `configure_styles()` method

Currently injects ~25 lines of CSS as a string:

```python
def configure_styles(self) -> None:
    ui.query('body').style('overflow: hidden; margin: 0; padding: 0;')
    ui.add_head_html('''
        <style>
            .year-select-popup .q-item, ...
        </style>
    ''')
```

### Proposed: Move to `frontend/assets/css/stamps-manager.css`

```css
.year-select-popup .q-item, 
.year-select-popup .q-item__label {
    color: black !important;
}
...
```

**Lines saved:** ~25 lines

---

## Priority 3: Consolidate Error Handling

The page has repeated patterns:

```python
if self._is_valid_response(response):
    # process
else:
    self.notify(...)
    self.log.error(...)
```

### Proposed: Add helper method

```python
def _handle_response(self, response, success_callback, error_key=None):
    if self._is_valid_response(response):
        return success_callback(response)
    else:
        error_msg = error_key or self.ERR_API
        self.notify(_(error_msg), 'warning', timeout=0, close_button=_('ui.close'))
        self.log.error(f'API error: {response.status_code if response else "No response"}')
```

**Lines saved:** ~20 lines

---

## Priority 4: Remove Unused Attributes

- `all_issues` - could be removed if we use `table.rows` instead
- Some class constants may be redundant

---

## Summary

| Priority | Item | Effort | Lines Saved |
|----------|------|--------|-------------|
| 1 | Extract Stamp Filters | Medium | ~80 lines |
| 2 | Move Styles to CSS | Low | ~25 lines |
| 3 | Consolidate Error Handling | Low | ~20 lines |
| 4 | Remove Unused Attributes | Low | ~10 lines |

**Total potential reduction:** ~135 lines from ~500 lines (~27%)
