# MEMORY LEAK FIX - React State Update Warnings

**Date:** 2025-11-16
**Issue:** React warnings in Dash app about state updates on unmounted components
**Root Cause:** dcc.Interval components continue after page navigation
**Status:** Fix documented, ready to apply

---

## 🔴 THE WARNING

```
Warning: Can't perform a React state update on unmounted component.
This is a no-op, but it indicates a memory leak in your application.
To fix, cancel all subscriptions and asynchronous tasks in the componentWillUnmount method.
```

---

## 📊 ROOT CAUSE ANALYSIS

### Why This Happens

**Dash uses React internally.** When you navigate between pages:

1. User starts a process (forecast, profile, or PyPSA)
2. `dcc.Interval` starts polling (enabled)
3. User navigates to different page
4. **OLD page unmounts** (components removed from DOM)
5. **Interval keeps running** (not properly cleaned up)
6. Interval callback fires and tries to update components on OLD page
7. **React error**: Can't update unmounted components!

### Problem Locations

All pages with progress tracking:
1. `dash/pages/demand_projection.py` - forecast-progress-interval
2. `dash/pages/generate_profiles.py` - prof-progress-interval
3. `dash/pages/model_config.py` - pypsa-progress-interval
4. `dash/app.py` - Global intervals (forecast-interval, profile-interval, pypsa-interval)

---

## ✅ THE FIX

### Strategy

**Disable intervals when page changes OR process completes**

Two approaches:
1. **Process-based**: Disable when process ends (CURRENT - partially working)
2. **Page-based**: Disable when page changes (NEEDED - missing)

### Current Implementation (Partial)

Intervals DO disable when process completes:

```python
@callback(
    Output('forecast-progress-interval', 'disabled'),
    Input('forecast-progress-interval', 'n_intervals'),
    State('forecast-process-state', 'data'),
    prevent_initial_call=True
)
def poll_forecast_progress(n, process_state):
    if not process_state or not process_state.get('process_id'):
        return True  # ✅ Disables when no process

    # ... check progress ...

    if progress.get('status') in ['completed', 'error']:
        return True  # ✅ Disables when complete

    return False  # Keeps polling
```

**Problem:** Doesn't handle page navigation!

---

## 🔧 COMPLETE FIX

### Fix #1: Add Page-Level Interval Control

**Add to each page with intervals:**

```python
# At top of layout function
def layout(active_project=None):
    return html.Div([
        # ... existing components ...

        # Add page mount/unmount detector
        dcc.Store(id='page-mounted', data=True, storage_type='memory'),

        # ... rest of layout ...
    ])

# Add cleanup callback
@callback(
    Output('forecast-progress-interval', 'disabled', allow_duplicate=True),
    Input('url', 'pathname'),  # Triggers when URL changes
    prevent_initial_call=False  # Must run on load
)
def cleanup_on_navigation(pathname):
    """Disable interval when navigating away from page."""
    if pathname != '/demand-projection':  # Not on this page
        return True  # Disable interval
    return dash.no_update
```

### Fix #2: Enhanced Poll Callbacks

**Improve existing poll callbacks:**

```python
@callback(
    Output('forecast-progress-interval', 'disabled'),
    Output('forecast-process-state', 'data'),
    Input('forecast-progress-interval', 'n_intervals'),
    State('forecast-process-state', 'data'),
    State('url', 'pathname'),  # ADD: Check current page
    prevent_initial_call=True
)
def poll_forecast_progress(n, process_state, pathname):
    # FIX #1: Check if still on correct page
    if pathname != '/demand-projection':
        return True, no_update  # Disable if navigated away

    # FIX #2: Check if process exists
    if not process_state or not process_state.get('process_id'):
        return True, no_update  # Disable if no process

    # Poll for progress
    try:
        progress = api.get_forecast_progress(process_state['process_id'])

        # FIX #3: Always disable on completion
        if progress.get('status') in ['completed', 'error', 'cancelled']:
            return True, progress  # Disable and return final state

        return False, progress  # Keep polling

    except Exception as e:
        # FIX #4: Disable on error
        logger.error(f"Poll error: {e}")
        return True, {'status': 'error', 'message': str(e)}
```

### Fix #3: Global App Cleanup

**In `dash/app.py`, add global cleanup:**

```python
# Add after existing callbacks

@callback(
    [
        Output('forecast-interval', 'disabled', allow_duplicate=True),
        Output('profile-interval', 'disabled', allow_duplicate=True),
        Output('pypsa-interval', 'disabled', allow_duplicate=True)
    ],
    Input('url', 'pathname'),
    prevent_initial_call=False
)
def cleanup_global_intervals(pathname):
    """
    Disable all global intervals when navigating.
    They will be re-enabled by page-specific callbacks if needed.
    """
    # Always disable global intervals on navigation
    # Individual pages will re-enable if they need them
    return True, True, True
```

---

## 📝 FILES TO MODIFY

### 1. `dash/pages/demand_projection.py`

**Lines to modify:** ~1818, ~2210

**Before:**
```python
@callback(
    Output('forecast-progress-interval', 'disabled'),
    Output('forecast-process-state', 'data'),
    Input('forecast-progress-interval', 'n_intervals'),
    State('forecast-process-state', 'data'),
    prevent_initial_call=True
)
def poll_forecast_progress(n, process_state):
    if not process_state or not process_state.get('process_id'):
        return True, no_update
    # ... rest ...
```

**After:**
```python
@callback(
    Output('forecast-progress-interval', 'disabled'),
    Output('forecast-process-state', 'data'),
    Input('forecast-progress-interval', 'n_intervals'),
    State('forecast-process-state', 'data'),
    State('selected-page-store', 'data'),  # ADD THIS
    prevent_initial_call=True
)
def poll_forecast_progress(n, process_state, current_page):
    # CRITICAL FIX: Stop polling if navigated away
    if current_page != 'Demand Projection':
        return True, no_update

    if not process_state or not process_state.get('process_id'):
        return True, no_update
    # ... rest ...
```

### 2. `dash/pages/generate_profiles.py`

**Lines to modify:** ~719

**Before:**
```python
@callback(
    [
        Output('prof-process-state', 'data', allow_duplicate=True),
        Output('prof-logs-store', 'data', allow_duplicate=True),
        Output('prof-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('prof-progress-interval', 'n_intervals'),
    [
        State('prof-process-state', 'data'),
        State('prof-logs-store', 'data')
    ],
    prevent_initial_call=True
)
def poll_sse_progress(n_intervals, process_state, current_logs):
    if not process_state or not process_state.get('isRunning'):
        return no_update, no_update, True
    # ... rest ...
```

**After:**
```python
@callback(
    [
        Output('prof-process-state', 'data', allow_duplicate=True),
        Output('prof-logs-store', 'data', allow_duplicate=True),
        Output('prof-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('prof-progress-interval', 'n_intervals'),
    [
        State('prof-process-state', 'data'),
        State('prof-logs-store', 'data'),
        State('selected-page-store', 'data')  # ADD THIS
    ],
    prevent_initial_call=True
)
def poll_sse_progress(n_intervals, process_state, current_logs, current_page):
    # CRITICAL FIX: Stop polling if navigated away
    if current_page != 'Generate Profiles':
        return no_update, no_update, True

    if not process_state or not process_state.get('isRunning'):
        return no_update, no_update, True
    # ... rest ...
```

### 3. `dash/pages/model_config.py`

**Lines to modify:** ~470

**Before:**
```python
@callback(
    [
        Output('pypsa-process-state', 'data', allow_duplicate=True),
        Output('pypsa-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('pypsa-progress-interval', 'n_intervals'),
    [
        State('pypsa-process-state', 'data'),
        State('active-project-store', 'data')
    ],
    prevent_initial_call=True
)
def poll_model_progress(n_intervals, process_state, active_project):
    if not process_state.get('isRunning'):
        return dash.no_update, True
    # ... rest ...
```

**After:**
```python
@callback(
    [
        Output('pypsa-process-state', 'data', allow_duplicate=True),
        Output('pypsa-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('pypsa-progress-interval', 'n_intervals'),
    [
        State('pypsa-process-state', 'data'),
        State('active-project-store', 'data'),
        State('selected-page-store', 'data')  # ADD THIS
    ],
    prevent_initial_call=True
)
def poll_model_progress(n_intervals, process_state, active_project, current_page):
    # CRITICAL FIX: Stop polling if navigated away
    if current_page != 'Model Config':
        return dash.no_update, True

    if not process_state.get('isRunning'):
        return dash.no_update, True
    # ... rest ...
```

### 4. `dash/app.py`

**Add new callback after line ~450:**

```python
# Add global interval cleanup
@callback(
    [
        Output('forecast-interval', 'disabled', allow_duplicate=True),
        Output('profile-interval', 'disabled', allow_duplicate=True),
        Output('pypsa-interval', 'disabled', allow_duplicate=True)
    ],
    Input('selected-page-store', 'data'),
    prevent_initial_call=False
)
def cleanup_intervals_on_navigation(current_page):
    """
    Disable all global intervals when user navigates.
    This prevents memory leaks from intervals trying to update unmounted components.
    Individual pages will re-enable their specific intervals as needed.
    """
    # Disable all intervals by default
    # Pages that need them will re-enable in their own callbacks
    return True, True, True
```

---

## 🧪 TESTING

### Test Scenario 1: Normal Operation
1. Start forecast on Demand Projection page
2. Wait for progress to show
3. Let it complete
4. **Expected:** Interval disables, no warnings

### Test Scenario 2: Navigation During Process
1. Start forecast on Demand Projection page
2. **Navigate to different page** while running
3. **Expected:**
   - Interval disables immediately
   - No React warnings
   - Process continues in background

### Test Scenario 3: Return to Page
1. Start forecast
2. Navigate away
3. **Navigate back** to Demand Projection
4. **Expected:**
   - Can see process status
   - Interval re-enables if process still running
   - No duplicate processes

### Verification

**Check browser console for:**
- ❌ NO "Can't perform a React state update" warnings
- ❌ NO "memory leak" messages
- ✅ Clean navigation between pages
- ✅ Progress tracking works correctly

---

## 📋 IMPLEMENTATION CHECKLIST

### Critical Fixes
- [ ] Add `State('selected-page-store', 'data')` to all poll callbacks
- [ ] Add page check at start of each poll callback
- [ ] Return `True` (disable) when not on correct page
- [ ] Add global cleanup callback in app.py

### Files to Modify
- [ ] `dash/pages/demand_projection.py` (line ~1818)
- [ ] `dash/pages/generate_profiles.py` (line ~719)
- [ ] `dash/pages/model_config.py` (line ~470)
- [ ] `dash/app.py` (add new callback after ~450)

### Testing
- [ ] Test forecast with navigation
- [ ] Test profile generation with navigation
- [ ] Test PyPSA with navigation
- [ ] Verify no console warnings
- [ ] Check process continues in background

---

## 🎯 IMPACT

**Before Fix:**
- ❌ React warnings on every navigation during process
- ❌ Memory leaks from orphaned intervals
- ❌ Potential performance degradation
- ❌ Console spam

**After Fix:**
- ✅ No React warnings
- ✅ Clean component unmounting
- ✅ No memory leaks
- ✅ Better performance
- ✅ Professional, polished experience

---

## 💡 ALTERNATIVE: Clientside Callbacks

For even better performance, consider clientside callbacks:

```python
app.clientside_callback(
    """
    function(pathname) {
        // Disable interval if not on demand projection page
        if (pathname !== '/demand-projection') {
            return true;  // Disable
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('forecast-progress-interval', 'disabled'),
    Input('url', 'pathname')
)
```

**Benefits:**
- Runs in browser (no server round-trip)
- Faster response
- Reduces server load

**Drawbacks:**
- JavaScript required
- Harder to debug
- Less Python-friendly

**Recommendation:** Use Python callbacks first, optimize to clientside later if needed.

---

**Status:** Ready to implement
**Priority:** HIGH (Fixes user-visible warnings)
**Effort:** 30 minutes
**Testing:** 15 minutes

**Total Time:** ~45 minutes to completely eliminate React warnings
