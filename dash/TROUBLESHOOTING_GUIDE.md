# DASH WEBAPP TROUBLESHOOTING GUIDE

**Date:** 2025-11-16
**Issue:** Buttons not working on Load Project, Create Project, and other pages

---

## 🔍 QUICK DIAGNOSIS

### What to Check First

1. **Check Browser Console (F12)**
   - Press F12 in your browser
   - Go to "Console" tab
   - Look for any red errors
   - Look for warnings about "callback" or "component"

2. **Check Terminal Output**
   - Look at the terminal where `python app.py` is running
   - Check for any errors or warnings
   - Look for "Callback error" messages

3. **Check if App Started Successfully**
   - After running `python app.py`, you should see:
     ```
     Dash is running on http://0.0.0.0:8050/
     ```
   - If you see errors before this, the app didn't start correctly

---

## 🐛 COMMON ISSUES & FIXES

### Issue 1: Navigation Buttons Don't Work

**Symptoms:**
- Clicking sidebar buttons does nothing
- Clicking "Create Project" or "Load Project" buttons doesn't navigate

**Cause:** Navigation callback using unsafe `eval()` function

**Fix Applied:** ✅ FIXED in latest commit
- Changed from `eval()` to `json.loads()` for safer parsing
- Added error handling for malformed button IDs

**Test:**
1. Click any sidebar menu item
2. Check browser console for errors
3. Page should navigate to selected section

---

### Issue 2: Create Project Button Does Nothing

**Symptoms:**
- Fill in project name and location
- Click "Create Project" button
- Nothing happens

**Possible Causes:**
1. **Invalid path** - Check path validation feedback
2. **Missing permissions** - Can't create folders
3. **Callback error** - Check browser console

**How to Debug:**
1. Open browser console (F12)
2. Click "Create Project" button
3. Look for errors in console
4. Check terminal output for Python errors

**Manual Test:**
```python
# Run this in Python to test if you can create folders
import os
test_path = "C:\\Users\\YourName\\Desktop\\test_project"  # Change this
os.makedirs(test_path, exist_ok=True)
print(f"✅ Successfully created: {test_path}")
```

---

### Issue 3: Buttons Work But Nothing Happens

**Symptoms:**
- Buttons respond to clicks (visual feedback)
- But no action occurs
- No errors in console

**Possible Causes:**
1. **Callback not registered** - Page not imported yet (lazy loading)
2. **Missing component ID** - Button references non-existent component
3. **Duplicate callback outputs** - Two callbacks trying to update same component

**How to Debug:**
Run the diagnostic script:
```bash
cd dash
python test_app.py
```

This will check for:
- Import errors
- Callback registration
- Duplicate outputs
- Page module issues

---

### Issue 4: "DuplicateCallback" Error

**Symptoms:**
- App crashes on startup
- Error mentions "allow_duplicate requires prevent_initial_call"

**Fix:** ✅ ALREADY FIXED
- Changed `prevent_initial_call=False` to `prevent_initial_call='initial_duplicate'`
- This was in the global interval cleanup callback

---

### Issue 5: "Store ID Not Found" Errors

**Symptoms:**
- Console shows errors about missing store IDs
- `sectors-store` or `color-config-store` conflicts

**Fix:** ✅ ALREADY FIXED
- Renamed duplicate store IDs in demand_visualization.py
- `sectors-store` → `viz-sectors-store`
- `color-config-store` → `viz-color-config-store`

---

## 🔧 MANUAL FIXES TO TRY

### Fix 1: Clear Browser Cache

Sometimes old JavaScript is cached:

1. Open browser
2. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
3. Select "Cached images and files"
4. Click "Clear data"
5. Refresh the page (`Ctrl + F5` or `Cmd + Shift + R`)

---

### Fix 2: Check Python Dependencies

Ensure all required packages are installed:

```bash
pip install dash==2.14.0
pip install dash-bootstrap-components==1.5.0
pip install plotly==5.18.0
pip install pandas openpyxl
```

---

### Fix 3: Run Diagnostic Script

```bash
cd dash
python test_app.py
```

This will:
- Check all imports
- Verify callbacks are registered
- Test page rendering
- Identify duplicate outputs

---

### Fix 4: Enable Debug Mode

Edit `app.py` at the bottom:

```python
if __name__ == '__main__':
    app.run_server(
        debug=True,  # ← Change this to True
        host='0.0.0.0',
        port=8050
    )
```

Debug mode shows:
- Detailed error messages
- Hot reloading on code changes
- Better stack traces

---

### Fix 5: Check Component IDs

If specific buttons don't work, verify the component ID exists:

1. Open browser developer tools (F12)
2. Go to "Elements" tab
3. Find the button using selector: `button[id*="your-button-name"]`
4. Check if the ID matches what the callback expects

---

## 📊 DIAGNOSTIC CHECKLIST

Use this checklist to systematically identify the issue:

- [ ] **App starts without errors**
  - No Python exceptions in terminal
  - See "Dash is running on..." message

- [ ] **Browser loads the page**
  - http://localhost:8050 shows homepage
  - No blank white screen

- [ ] **Console shows no errors**
  - Press F12 → Console tab
  - No red error messages

- [ ] **Navigation works**
  - Sidebar menu items are clickable
  - Clicking changes the page content

- [ ] **Home page statistics load**
  - See project count
  - See forecast/profile counts (if project loaded)

- [ ] **Create Project page loads**
  - Click "Create Project" in sidebar
  - Form appears with name/location fields

- [ ] **Path validation works**
  - Type a folder path
  - See green checkmark or red error

- [ ] **Create Project button responds**
  - Fill in name and location
  - Click "Create Project"
  - See success modal OR error message

- [ ] **Load Project page loads**
  - Click "Load Project" in sidebar
  - See project path input field

---

## 🚨 ERROR MESSAGES & SOLUTIONS

### "Cannot find module 'dash'"

**Solution:**
```bash
pip install dash dash-bootstrap-components plotly
```

---

### "Callback error: Output 'X' not found in layout"

**Cause:** Callback references a component that doesn't exist

**Solution:**
1. Check if component ID matches callback Output ID
2. Ensure component is in the current page's layout
3. Check for typos in component IDs

---

### "Duplicate callback output: X.children"

**Cause:** Two callbacks trying to update the same component

**Solution:**
1. Use `allow_duplicate=True` on one callback
2. Or combine the callbacks into one
3. Check for callbacks in both app.py and page modules

---

### "prevent_initial_call must be True when using allow_duplicate"

**Cause:** Using `allow_duplicate=True` with `prevent_initial_call=False`

**Solution:** Change to:
```python
@callback(
    Output('component-id', 'property', allow_duplicate=True),
    ...,
    prevent_initial_call='initial_duplicate'  # ← Use this special value
)
```

---

### "React state update on unmounted component"

**Cause:** dcc.Interval continues running after navigating away

**Solution:** ✅ ALREADY FIXED
- Added page-aware polling in all callbacks
- Intervals stop when navigating away from page

---

## 🎯 SPECIFIC PAGE FIXES

### Create Project Page

**Common Issues:**

1. **Browse button doesn't work**
   - ✅ FIXED: Replaced with tooltip guide
   - Use manual path entry instead

2. **Path validation fails**
   - Check path exists on your system
   - Use forward slashes `/` or escaped backslashes `\\`
   - Example: `C:\\Users\\YourName\\Documents`

3. **"Template files not found" warning**
   - Check if `backend_fastapi/input/` folder exists
   - Should contain:
     - `input_demand_file.xlsx`
     - `load_curve_template.xlsx`
     - `pypsa_input_template.xlsx`

---

### Load Project Page

**Common Issues:**

1. **Project not found**
   - Enter the FULL path to project folder
   - Project folder must contain `project.json`

2. **"Invalid project structure"**
   - Project must have:
     - `inputs/` folder
     - `results/` folder
     - `project.json` file

3. **Recent projects list empty**
   - Create a project first
   - Or load an existing project
   - List is stored in browser localStorage

---

## 📞 GETTING MORE HELP

If issues persist:

1. **Collect Error Information:**
   - Screenshot of browser console (F12 → Console)
   - Terminal output from `python app.py`
   - Steps to reproduce the issue

2. **Check Version Compatibility:**
   ```bash
   python --version  # Should be 3.8+
   pip show dash     # Should be 2.14.0+
   ```

3. **Try Clean Install:**
   ```bash
   pip uninstall dash dash-bootstrap-components plotly
   pip install dash==2.14.0 dash-bootstrap-components==1.5.0 plotly==5.18.0
   ```

4. **Run in Debug Mode:**
   - Edit `app.py`: change `debug=False` to `debug=True`
   - Restart app
   - Check for detailed error messages

---

## ✅ RECENT FIXES APPLIED

### November 16, 2025

1. ✅ **Fixed duplicate store IDs**
   - Renamed stores in demand_visualization.py
   - Prevents state corruption between pages

2. ✅ **Fixed navigation callback**
   - Replaced unsafe `eval()` with `json.loads()`
   - Added error handling for malformed button IDs

3. ✅ **Fixed interval cleanup**
   - Changed `prevent_initial_call=False` to `'initial_duplicate'`
   - Resolves DuplicateCallback error

4. ✅ **Added dynamic statistics**
   - Home page now shows real project/forecast/profile counts
   - Scans filesystem for accurate data

5. ✅ **Fixed browse button UX**
   - Replaced non-functional button with helpful tooltip
   - Clear instructions for getting folder paths

---

## 🎓 UNDERSTANDING THE ARCHITECTURE

### How Navigation Works

1. User clicks a navigation button with ID: `{'type': 'nav-link', 'page': 'Create Project'}`
2. `navigate_to_page` callback fires
3. Extracts page name from button ID
4. Updates `selected-page-store` with page name
5. `render_page_content` callback detects the change
6. Lazy-loads the page module (first time only)
7. Returns page layout as main content

### How Callbacks Are Registered

1. **App.py callbacks:** Registered when app starts
2. **Page callbacks:** Registered when page module is imported (lazy loading)
3. **First visit:** Page import triggers callback registration
4. **Subsequent visits:** Callbacks already registered, just render layout

### How State Is Managed

- `dcc.Store(storage_type='session')` - Lasts until browser tab closes
- `dcc.Store(storage_type='local')` - Persists across sessions
- `dcc.Store(storage_type='memory')` - Clears on page refresh

---

**End of Troubleshooting Guide**

For the latest updates and fixes, check the git commit history:
```bash
git log --oneline | head -10
```
