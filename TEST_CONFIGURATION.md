# Test Configuration Guide

## Final Configuration: pytest-only

After testing both pytest and Django test runner configurations, we've determined that **pytest-only** configuration works best for VS Code test discovery. Running both pytest and Django test runner simultaneously causes conflicts in VS Code Test Explorer.

## Current Configuration

### VS Code Settings (`.vscode/settings.json`)
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
}
```

### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = tests.py test_*.py *_tests.py
python_classes = *Test* *TestCase
python_functions = test_*
addopts = --verbose --tb=short --reuse-db
testpaths = apps
filterwarnings =
    ignore::django.utils.deprecation.RemovedInDjango50Warning
    ignore::DeprecationWarning
markers =
    django_db: mark test to use django database
minversion = 6.0
```

## Test Structure

All tests are in `apps/inventory/tests.py` with 42 test methods across 12 test classes:

1. **UserModelTest** - Tests for custom User model
2. **CategoryModelTest** - Tests for hierarchical Category model
3. **SupplierModelTest** - Tests for Supplier model
4. **ProductModelTest** - Tests for Product model with relationships
5. **CategoryProductRelationshipTest** - Integration tests for category-product relationships
6. **ModelIntegrationTest** - Complete integration tests
7. **MockDataTestCase** - Tests using mock data factory
8. **AdvancedModelTestCase** - Edge cases and error handling
9. **DatabaseTransactionTestCase** - Transaction-specific tests
10. **MockedExternalServiceTestCase** - Tests with mocked external services
11. **PerformanceTestCase** - Performance and optimization tests
12. **EdgeCaseTestCase** - Boundary conditions and edge cases
13. **FixtureTestCase** - Tests using predefined fixtures

## Running Tests

### Command Line
```bash
# Run all tests
virtualEnvironment/bin/pytest apps/inventory/tests.py

# Run with verbose output
virtualEnvironment/bin/pytest apps/inventory/tests.py -v

# Run specific test class
virtualEnvironment/bin/pytest apps/inventory/tests.py::UserModelTest

# Run specific test method
virtualEnvironment/bin/pytest apps/inventory/tests.py::UserModelTest::test_create_user
```

### VS Code Test Explorer
- Open Command Palette (`Ctrl+Shift+P`)
- Run "Python: Refresh Tests"
- Tests should appear in Test Explorer
- Click individual tests or use "Run All Tests" button

### Django Management Command (Alternative)
```bash
# You can still use Django's test runner if needed
python manage.py test apps.inventory.tests
```

## Dependencies

Required packages (already in `requirements.txt`):
- `pytest>=7.4.0`
- `pytest-django>=4.7.0`

## Key Benefits of pytest Configuration

1. **Better test discovery**: Finds all test methods reliably
2. **Rich assertions**: Better error messages than unittest
3. **Fixtures**: Powerful fixture system for test data
4. **Plugins**: Extensive plugin ecosystem
5. **Parametrization**: Easy test parametrization
6. **Reporting**: Better test reporting and output formatting

## Troubleshooting

If tests don't appear in VS Code Test Explorer:
1. Check that `python.testing.pytestEnabled` is `true`
2. Check that `python.testing.unittestEnabled` is `false`
3. Refresh tests: `Ctrl+Shift+P` -> "Python: Refresh Tests"
4. Check Python interpreter: `Ctrl+Shift+P` -> "Python: Select Interpreter"
5. Restart VS Code if needed

For detailed troubleshooting, see `VS_CODE_TEST_TROUBLESHOOTING.md`.
