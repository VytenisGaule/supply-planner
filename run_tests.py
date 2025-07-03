#!/usr/bin/env python
"""
Custom pytest runner for VS Code Django test discovery
"""
import os
import sys
import django

def setup_django():
    """Initialize Django before running tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

if __name__ == "__main__":
    setup_django()
    
    # Import pytest after Django is set up
    import pytest
    
    # Default arguments for pytest
    pytest_args = [
        'app/tests.py',
        '-v',
        '--tb=short',
        '--reuse-db'
    ]
    
    # Add any additional arguments passed from command line
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)
