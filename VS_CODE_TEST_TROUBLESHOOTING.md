# VS Code Test Discovery Troubleshooting Guide

## Issue: Tests run but individual test methods not shown in Test Explorer

### Step 1: Verify Current Configuration

Check these files exist and have correct content:
- `.vscode/settings.json` ✓
- `pytest.ini` ✓  
- `pyproject.toml` ✓
- `.env` ✓

### Step 2: Manual VS Code Commands

Try these commands in VS Code Command Palette (`Ctrl+Shift+P`):

1. **"Developer: Reload Window"** 
   - This reloads VS Code with new settings

2. **"Python: Select Interpreter"**
   - Choose: `./virtualEnvironment/bin/python`

3. **"Python: Configure Tests"**
   - Select "pytest"
   - Choose workspace folder as root directory

4. **"Test: Reset and Reload All Test Data"**
   - Forces VS Code to rediscover all tests

5. **"Python: Refresh Tests"**
   - Manually refresh test discovery

### Step 3: Check Test Explorer Panel

1. Open Test Explorer: View → Testing (or Ctrl+Shift+T)
2. Look for the beaker/flask icon in left sidebar
3. Click refresh button in Test Explorer panel
4. Expand the test tree to see individual methods

### Step 4: Verify Test Discovery

Run this command in terminal to verify pytest can discover all tests:

```bash
python -m pytest apps/inventory/tests.py --collect-only
```

Expected output: Should show all 42 test methods organized by class.

### Step 5: Check VS Code Output Panel

1. Open Output panel: View → Output
2. Select "Python Test Log" from dropdown
3. Look for any error messages about test discovery

### Step 6: Alternative: Use Test Commands

If Test Explorer doesn't work, you can still run tests via Command Palette:

- `Ctrl+Shift+P` → "Python: Run All Tests"
- `Ctrl+Shift+P` → "Python: Debug All Tests"  
- `Ctrl+Shift+P` → "Python: Run Current Test File"

### Step 7: Manual Test Execution

You can always run tests manually in terminal:

```bash
# All tests
python -m pytest apps/inventory/tests.py -v

# Specific test class
python -m pytest apps/inventory/tests.py::UserModelTest -v

# Specific test method
python -m pytest apps/inventory/tests.py::UserModelTest::test_create_user -v

# Django test runner
python manage.py test apps.inventory.tests.UserModelTest.test_create_user
```

### Step 8: Check Extension Installation

Install these extensions if not already installed:

1. **Python** (ms-python.python) ✓ Already installed
2. **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter)
3. **Test Explorer UI** (hbenl.vscode-test-explorer)

### Step 9: Debug Mode

Enable VS Code Python extension logging:

1. `Ctrl+Shift+P` → "Python: Enable Logging"
2. Run test discovery
3. Check logs in Output panel

### Step 10: Workspace Settings Check

Verify these settings in `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "apps/inventory/tests.py",
        "-v",
        "--tb=short"
    ],
    "python.testing.autoTestDiscoverOnSaveEnabled": true,
    "python.testing.cwd": "${workspaceFolder}",
    "python.envFile": "${workspaceFolder}/.env"
}
```

## Common Issues and Solutions

### Issue 1: Python Interpreter Not Found
**Solution**: Set correct interpreter path to `./virtualEnvironment/bin/python`

### Issue 2: Django Not Configured  
**Solution**: Ensure `DJANGO_SETTINGS_MODULE=core.settings` in `.env`

### Issue 3: Tests Found But Methods Not Expanded
**Solution**: 
- Try disabling unittest and enabling only pytest
- Clear VS Code workspace cache
- Restart VS Code

### Issue 4: Import Errors
**Solution**: Ensure virtual environment is activated and all dependencies installed

## Test Structure Overview

Your test file contains:
- **10 Test Classes**
- **42 Individual Test Methods**
- **Mock Data Factory** for realistic test data
- **Integration, Performance, and Edge Case Tests**

## Current Test Classes:

1. `UserModelTest` (3 methods)
2. `CategoryModelTest` (7 methods)  
3. `SupplierModelTest` (2 methods)
4. `ProductModelTest` (6 methods)
5. `CategoryProductRelationshipTest` (1 method)
6. `ModelIntegrationTest` (3 methods)
7. `MockDataTestCase` (5 methods)
8. `AdvancedModelTestCase` (4 methods)
9. `MockedExternalServiceTestCase` (2 methods)
10. `PerformanceTestCase` (2 methods)
11. `EdgeCaseTestCase` (3 methods)
12. `FixtureTestCase` (2 methods)
13. `DatabaseTransactionTestCase` (2 methods)

If you continue having issues, try switching to purely pytest-based testing or using the manual terminal commands.

## Updated Solution: Django Import Error Fix

**Problem:** VS Code shows import errors when trying to discover tests:
```
ERROR collecting apps/inventory/tests.py
apps/inventory/tests.py:8: in <module>
    from apps.inventory.models import User, Category, Product, Supplier
```

**Root Cause:** Django isn't properly initialized when VS Code's test extension tries to discover tests.

### Latest Fix Applied ✅

1. **Enhanced conftest.py** that properly initializes Django:
```python
import os
import django

def pytest_configure():
    """Configure Django settings for pytest"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
```

2. **Updated pytest.ini** with explicit Django settings:
```ini
addopts = --verbose --tb=short --reuse-db --ds=core.settings
```

3. **Enhanced VS Code settings** with environment variables:
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "apps/inventory/tests.py",
        "-v",
        "--tb=short",
        "--ds=core.settings"
    ],
    "python.testing.env": {
        "DJANGO_SETTINGS_MODULE": "core.settings"
    }
}
```

4. **Custom test runner** (`run_tests.py`) as fallback:
```bash
# Use if VS Code test discovery still fails
virtualEnvironment/bin/python run_tests.py --collect-only
```

### Verification Commands

```bash
# This should work now and show 42 tests
virtualEnvironment/bin/pytest --collect-only apps/inventory/tests.py

# This should run all tests successfully  
virtualEnvironment/bin/pytest apps/inventory/tests.py -v
```

**Status**: ✅ Configuration updated to fix Django import issues
