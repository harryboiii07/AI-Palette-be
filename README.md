# FlavorForge Backend API

AI-powered product development platform for FMCG companies that helps create and analyze consumer packaged goods using market insights and AI recommendations.

## Technology Stack

- **Framework**: FastAPI
- **Data Processing**: Pandas
- **Data Source**: CSV files
- **Validation**: Pydantic models

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Place your CSV files in the `data/` directory:
   - `dashboard_metrics.csv` - Business metrics and KPI data
   - `products.csv` - Product catalog with market scores
   - `market_trends.csv` - Ingredient popularity and trends
   - `competitors.csv` - Competitor analysis data
   - `analysis_results.csv` - AI analysis results

3. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Endpoints

### Dashboard Metrics
`GET /api/dashboard/metrics`

Query parameters:
- `timeframe`: Time period (7d, 30d, 90d) - default: 30d
- `region`: Filter by region (optional)

Returns dashboard metrics including total products, success rates, active users, and growth metrics.

## CSV File Structure

### dashboard_metrics.csv
Required columns:
- `metric_name`: Name of the metric (total_products, success_rate, active_users, trending_categories)
- `metric_value`: Numeric value of the metric
- `growth_percentage`: Growth percentage for the metric
- `timeframe`: Time period (7d, 30d, 90d)
- `region`: Geographic region (Global, North America, Europe, Asia, etc.)
- `date_recorded`: Date when the metric was recorded

Example structure:
```csv
metric_name,metric_value,growth_percentage,timeframe,region,date_recorded
total_products,250.0,8.5,30d,Global,2024-08-15
success_rate,87.5,3.2,30d,Global,2024-08-15
active_users,1450.0,8.1,30d,Global,2024-08-15
trending_categories,6.0,0.0,30d,Global,2024-08-15
```
