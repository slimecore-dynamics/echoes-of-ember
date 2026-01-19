# Investigation System - Code Review & Potential Issues

## Critical Issues Found

### 1. **CRITICAL: Save/Load Investigation Object Duplication**
**File:** `exploration/tiled_importer.rpy` + `investigation/investigation_persistence.rpy`

**Problem:**
When loading a save file, the system:
1. Loads `investigation_state` from JSON (with terminals/examinables)
2. Calls `reload_dungeon_layout()` which calls `load_tiled_map()`
3. `load_tiled_map()` re-registers all terminals/examinables, overwriting the loaded state

**Impact:**
- Terminals/examinables lose their saved state
- Any dynamically added terminal entries are lost
- `_cached_content` is reset (minor performance impact)

**Solution Needed:**
Add a parameter to `load_tiled_map()` to skip investigation object registration during reload:
```python
def load_tiled_map(filepath, floor_id=None, floor_name=None, reload_mode=False):
    # ...
    if not reload_mode and icon_type in ["terminal", "examinable"]:
        # Only register on initial load, not on reload
```

---

### 2. **Memory Management: Cached Content Never Cleared**
**Files:** `investigation/investigation_data.rpy`

**Problem:**
`ExaminableObject` and `TerminalEntry` cache content via `_cached_content`, but this cache is never cleared.

**Impact:**
- Content files remain in memory indefinitely
- Multiplied by number of terminals/examinables
- Can grow significantly in large games

**Current State:**
- Low priority for current scope
- Only becomes issue with 100+ objects

**Potential Solution:**
```python
def clear_content_cache(self):
    """Clear cached content to free memory."""
    self._cached_content = None
```

---

## Ren'Py Standards & Best Practices

### 1. **Screen Parameter Execution**
**File:** `investigation/investigation_screens.rpy:298`

**Current:**
```python
$ handle_terminal_entry_collection(terminal.id, entry.id)
```

**Analysis:**
- Executes every frame the screen is shown
- Could be called multiple times per second
- Function has early return for duplicates, so safe
- **Verdict: Acceptable**, but consider using `on "show"` properly if performance becomes an issue

---

### 2. **Global State Modifications in Screens**
**Files:** Multiple screen files

**Current Practice:**
```python
SetVariable("investigation_state.current_terminal_category", category)
```

**Analysis:**
- Directly modifying global state from UI
- Standard Ren'Py pattern, but less testable
- **Verdict: Acceptable for Ren'Py**, consider encapsulation for larger projects

---

### 3. **Error Handling: Silent Failures**
**Files:** `investigation/investigation_handlers.rpy`, `investigation/investigation_loader.rpy`

**Current:**
```python
if not terminal:
    return  # Silent failure
```

**Recommendation:**
Consider logging to file for debugging:
```python
if not terminal:
    import sys
    print("Warning: Terminal not found: {}".format(terminal_id), file=sys.stderr)
    return
```

---

## Integration Points & Future Hooks

### 1. **Story Conditional System**
**File:** `investigation/investigation_state.rpy:80-92`

**Current API:**
```python
has_evidence(item_id)
has_data(item_id)
has_collected(item_id)
```

**Recommendations:**
- ✅ Good: Clear, simple API
- ⚠️ Consider: Add `has_all_evidence([id1, id2])` for complex conditionals
- ⚠️ Consider: Add `get_collected_count()` for progress tracking

---

### 2. **Dynamic Content Addition**
**File:** `investigation/investigation_state.rpy:102-113`

**Current:**
```python
def add_terminal_entry(self, terminal_id, category, entry):
    terminal = self.get_terminal(terminal_id)
    if terminal:
        terminal.add_entry(entry)
```

**Issues:**
- ✅ Properly saves with state serialization
- ❌ No validation that category exists in TERMINAL_CATEGORIES
- ❌ No way to remove entries
- ⚠️ Entries added after load may have `_cached_content = None`

**Recommendations:**
```python
def remove_terminal_entry(self, terminal_id, entry_id):
    """Remove an entry (for story events)."""

def clear_terminal_category(self, terminal_id, category):
    """Clear all entries in a category."""
```

---

### 3. **Terminal State Persistence**
**Files:** `investigation/investigation_screens.rpy`

**Current:**
```python
investigation_state.current_terminal = terminal
investigation_state.current_terminal_category = None
investigation_state.current_terminal_entry_index = None
```

**Issue:**
- These are NOT saved in `to_dict()`
- Terminal UI state is lost on save/load
- **Impact:** Player must re-navigate terminal after load

**Recommendation:**
Either:
1. Add to `to_dict()` (saves UI state)
2. Reset to None on terminal interaction (intentional)

Current behavior is probably correct (fresh start each time).

---

## Potential Future Bugs

### 1. **Duplicate Item IDs Across Systems**
**Risk:** Medium

If exploration system adds items with same IDs as investigation items:
```python
# exploration collects item "key_card_01"
# investigation has terminal entry "key_card_01"
# collected_items set will have both!
```

**Solution:**
Use prefixed IDs:
- Investigation: `"inv_terminal_security_email_01"`
- Exploration: `"exp_key_card_01"`

---

### 2. **Journal Entry Ordering**
**File:** `investigation/investigation_state.rpy:72`

**Current:**
```python
self.journal_entries.append(entry)
```

**Issue:**
- Entries are in collection order
- No sorting by location or timestamp
- Could become messy with 50+ entries

**Recommendation:**
Add sorting option to `get_all_entries()`:
```python
def get_all_entries(self, sort_by="location"):
    entries = self.journal_entries
    if sort_by == "location":
        return sorted(entries, key=lambda e: e.location)
    elif sort_by == "time":
        return sorted(entries, key=lambda e: e.timestamp)
    return entries
```

---

### 3. **Content File Path Resolution**
**Files:** `investigation/investigation_data.rpy`

**Current:**
```python
renpy.file(self.content_file).read().decode('utf-8')
```

**Issue:**
- No validation that file exists before JSON save
- Paths are relative to game directory
- No fallback for missing files (except try/except)

**Recommendation:**
- Validate paths during JSON loading
- Consider bundling validation tool

---

### 4. **FPV Position Scaling**
**File:** `investigation/investigation_handlers.rpy:97-137`

**Current:**
```python
def calculate_fpv_position(distance, view_distance, fpv_width, fpv_height, custom_position=None):
```

**Potential Issue:**
- If `view_distance` changes between saves
- Custom positions might be off-screen
- No validation of custom_position bounds

**Low Risk:** View distance unlikely to change

---

## Performance Considerations

### 1. **Terminal Entry Search: O(n*m)**
**File:** `investigation/investigation_handlers.rpy:206-213`

**Current:**
```python
for category, entries in terminal.entries.items():
    for e in entries:
        if e.id == entry_id:
```

**Analysis:**
- Nested loop for every entry view
- Acceptable for <100 entries per terminal
- **Verdict: Low priority optimization**

---

### 2. **Journal Filtering**
**File:** `investigation/investigation_state.rpy:94-100`

**Current:**
```python
def get_evidence_entries(self):
    return [entry for entry in self.journal_entries if entry.entry_type == "evidence"]
```

**Analysis:**
- List comprehension on every screen refresh
- Acceptable for <500 entries
- **Verdict: Low priority optimization**

---

## Code Quality & Maintainability

### Strengths ✅
1. Clear separation of concerns (data, state, handlers, screens)
2. Consistent naming conventions
3. Good use of docstrings
4. Proper error handling with try/except
5. Save/load serialization implemented
6. Content cached appropriately

### Improvements ⚠️
1. Add type hints (Python 3.5+): `def collect_item(self, item_id: str, ...) -> bool:`
2. Add unit test helpers
3. Consider enum for entry_type: `EntryType.EVIDENCE` vs `"evidence"`
4. Add validation for required fields in from_dict()

---

## Recommendations Priority

### High Priority
1. ✅ **DONE:** Remove debug logs
2. ✅ **DONE:** Improve error handling (skip broken icons)
3. ⚠️ **TODO:** Fix save/load duplication bug (#1 Critical Issue)

### Medium Priority
4. Add entry ID prefixing convention
5. Add more helper functions for story (has_all_evidence, etc.)
6. Improve journal entry sorting

### Low Priority
7. Add content cache clearing
8. Optimize terminal entry search
9. Add type hints
10. Add validation helpers

---

## Testing Checklist

When other systems hook into this:

- [ ] Test with 50+ terminals/examinables (memory usage)
- [ ] Test save/load cycle preserves all data
- [ ] Test dynamically added terminal entries persist
- [ ] Test duplicate item IDs across systems
- [ ] Test missing content files don't crash
- [ ] Test empty categories work correctly
- [ ] Test journal with 100+ entries (performance)
- [ ] Test FPV overlays at different view distances
- [ ] Test interaction detection at map boundaries
- [ ] Test screen state after quick save/load cycles

---

## Conclusion

**Overall Assessment:** The investigation system is well-structured and follows good Ren'Py practices. The critical save/load bug needs fixing, but otherwise the code is production-ready for a visual novel game.

**Maintainability Score:** 8/10
**Performance Score:** 9/10
**Integration Risk:** Low (with save/load fix)
