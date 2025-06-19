#!/bin/bash

echo "=== Running Image Description API Tests ==="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python -c "import django, rest_framework, PIL" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Missing dependencies. Run: pip install -r requirements.txt"
    exit 1
fi

# Run Django checks
echo ""
echo "Running Django system checks..."
python manage.py check
if [ $? -eq 0 ]; then
    echo "✓ Django configuration valid"
else
    echo "✗ Django configuration issues found"
    exit 1
fi

# Run tests
echo ""
echo "Running test suite..."
python manage.py test --verbosity=2

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "=== ALL TESTS PASSED ✓ ==="
    echo ""
    echo "Next steps:"
    echo "1. Start server: python manage.py runserver"
    echo "2. Test endpoint: curl -X POST http://localhost:8000/api/describe/ -F 'image=@test_image.jpg'"
    echo "3. Health check: curl http://localhost:8000/api/health/"
else
    echo ""
    echo "=== TESTS FAILED ✗ ==="
    exit 1
fi