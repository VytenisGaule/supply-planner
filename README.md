# Stock Planner

A Django-based inventory management and stock prediction system designed for efficient inventory planning and purchase optimization.

## Features

### Core Functionality
- **Product Management**: Hierarchical product categories with supplier relationships
- **Daily Metrics Tracking**: Sales and stock level monitoring
- **Inventory Optimization**: Automated purchase recommendations
- **Supplier Management**: Multi-supplier product relationships

### Models
- **User**: Custom user model for authentication
- **Category**: Hierarchical product categorization
- **Product**: Core product information with lead times and pricing
- **Supplier**: Supplier management with product relationships
- **DailyMetrics**: Daily sales and stock tracking

### Key Features
- Hierarchical category structure with parent-child relationships
- Many-to-many supplier-product relationships
- Daily sales and stock level tracking
- Average daily purchase calculations
- Efficient bulk data import/update capabilities

## Tech Stack

- **Backend**: Django 4.x
- **Database**: PostgreSQL
- **Frontend**: Django Admin (customized)
- **Styling**: Tailwind CSS
- **Testing**: pytest-django
- **Data Processing**: Pandas (for CSV imports)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vytenis/stockPlanner.git
cd stockPlanner
```

2. Create and activate virtual environment:
```bash
python -m venv virtualEnvironment
source virtualEnvironment/bin/activate  # On Windows: virtualEnvironment\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure database settings in `core/settings.py`

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

## Usage

### Available Management Commands

```bash
# Import daily sales/stock data
python manage.py import_daily_data --csv data.csv

# Generate test data
python manage.py import_daily_data --generate-test-data --days 90

# Generate purchase recommendations
python manage.py generate_purchase_recommendations --report

# Test supplier relationships
python manage.py test_suppliers --list-all
```

### Available VS Code Tasks

- **Install Dependencies**: `pip install -r requirements.txt`
- **Django: Migrate**: Run database migrations
- **Django: Run Server**: Start development server
- **Run Tests**: Execute pytest test suite
- **Tailwind: Build**: Compile Tailwind CSS

## Project Structure

```
stock predictor/
├── app/                     # Main application
│   ├── models.py           # Core models
│   ├── admin.py            # Admin interface
│   ├── views.py            # Views
│   ├── management/         # Management commands
│   └── migrations/         # Database migrations
├── core/                   # Django project settings
├── static/                 # Static files
├── templates/              # Templates
├── logs/                   # Application logs
└── requirements.txt        # Python dependencies
```

## Data Models

### Product
- Product code and name
- Category assignment
- Supplier relationships
- Pricing and lead time information
- Average daily purchase calculations

### DailyMetrics
- Daily sales quantities
- Daily stock levels
- Unique constraint on (product, date)

### Category
- Hierarchical structure
- Parent-child relationships
- Automatic level calculation

### Supplier
- Company information
- Product relationships via many-to-many

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Development Status

This project is in active development. Current focus areas:
- Inventory optimization algorithms
- Data import/export capabilities
- Purchase recommendation system
- Performance optimization for large datasets
