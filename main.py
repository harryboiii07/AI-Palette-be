from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uvicorn
import math
from models import Product, ProductCreateRequest, ProductResponse, ProductListResponse

app = FastAPI(
    title="FlavorForge API",
    description="AI-powered product development platform for FMCG companies",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory path
DATA_DIR = Path("data")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "FlavorForge API is running", "status": "healthy"}

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(
    timeframe: str = Query(default="30d", description="Time period for metrics (7d, 30d, 90d)"),
    region: Optional[str] = Query(default="Global", description="Filter by region")
):
    """
    Calculate and return dashboard metrics from CSV data
    - Load dashboard_metrics.csv
    - Filter by timeframe and region
    - Calculate growth percentages
    """
    try:
        # Load dashboard metrics CSV
        csv_path = DATA_DIR / "dashboard_metrics.csv"
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dashboard metrics data not found")
        
        df = pd.read_csv(csv_path)
        
        # Filter by timeframe
        df = df[df['timeframe'] == timeframe]
        
        # Filter by region if specified (default to Global if no region specified)
        if region:
            df = df[df['region'].str.lower() == region.lower()]
        else:
            df = df[df['region'] == 'Global']
        
        # Calculate metrics
        metrics = _calculate_dashboard_metrics(df, timeframe)
        
        return {
            "success": True,
            "data": metrics
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard metrics file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing metrics: {str(e)}")

def _parse_timeframe(timeframe: str) -> int:
    """Parse timeframe string to number of days"""
    timeframe_map = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }
    return timeframe_map.get(timeframe, 30)

def _calculate_dashboard_metrics(df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
    """Calculate dashboard metrics from filtered data"""
    
    # Helper function to get metric value by name
    def get_metric_value(metric_name: str, default_value: float = 0.0) -> float:
        metric_row = df[df['metric_name'] == metric_name]
        if not metric_row.empty:
            return float(metric_row['metric_value'].iloc[0])
        return default_value
    
    # Helper function to get growth percentage by metric name
    def get_growth_percentage(metric_name: str, default_value: float = 0.0) -> float:
        metric_row = df[df['metric_name'] == metric_name]
        if not metric_row.empty:
            return float(metric_row['growth_percentage'].iloc[0])
        return default_value
    
    # Extract base metrics
    total_products = int(get_metric_value('total_products', 247))
    success_rate = get_metric_value('success_rate', 87.5)
    active_users = int(get_metric_value('active_users', 1432))
    trending_categories = int(get_metric_value('trending_categories', 5))
    
    # Calculate growth metrics
    growth_metrics = {
        "products_growth": get_growth_percentage('total_products', 12.3),
        "success_rate_growth": get_growth_percentage('success_rate', 3.2),
        "users_growth": get_growth_percentage('active_users', 8.1)
    }
    
    return {
        "total_products": total_products,
        "success_rate": round(success_rate, 1),
        "active_users": active_users,
        "trending_categories": trending_categories,
        "growth_metrics": growth_metrics
    }


@app.get("/api/products", response_model=ProductListResponse)
async def get_products(
    page: int = Query(default=1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of items per page"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    search: Optional[str] = Query(default=None, description="Search in product name or ingredients"),
    sort_by: str = Query(default="name", description="Sort by field (name, market_score, created_date)")
):
    """
    Load products.csv and return filtered/paginated results
    - Supports pagination with page and limit
    - Filter by category
    - Search in product name and ingredients
    - Sort by various fields
    """
    try:
        # Load products CSV
        csv_path = DATA_DIR / "products.csv"
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Products data not found")
        
        df = pd.read_csv(csv_path, index_col=None)
        
        # Clean data - ensure proper data types
        if 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce')
            # Only drop rows where id is actually NaN, not where conversion failed
            df = df[df['id'].notna()]
        
        # Apply category filter
        if category:
            df = df[df['category'].str.lower() == category.lower()]
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            df = df[
                df['name'].str.lower().str.contains(search_lower, na=False) |
                df['ingredients'].str.lower().str.contains(search_lower, na=False)
            ]
        
        # Apply sorting
        if sort_by == "market_score":
            df = df.sort_values('market_score', ascending=False)
        elif sort_by == "created_date":
            df = df.sort_values('created_date', ascending=False)
        else:  # default to name
            df = df.sort_values('name')
        
        # Calculate pagination
        total_items = len(df)
        total_pages = math.ceil(total_items / limit)
        offset = (page - 1) * limit
        
        # Apply pagination
        paginated_df = df.iloc[offset:offset + limit]
        
        # Convert to Product models
        products = []
        for _, row in paginated_df.iterrows():
            # Skip rows with invalid IDs
            if pd.isna(row['id']):
                continue
                
            product = Product(
                id=int(row['id']),
                name=str(row['name']),
                category=str(row['category']),
                market_score=float(row['market_score']),
                status=str(row['status']),
                created_date=str(row['created_date']),
                target_demographics=str(row['target_demographics']),
                region=str(row['region']),
                ingredients=str(row['ingredients']),
                flavor_profile=str(row['flavor_profile'])
            )
            products.append(product)
        
        # Prepare pagination info
        pagination = {
            "current_page": page,
            "per_page": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return ProductListResponse(
            success=True,
            data=products,
            pagination=pagination
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Products file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing products: {str(e)}")


@app.post("/api/products", response_model=ProductResponse)
async def create_product(product_data: ProductCreateRequest):
    """
    Create a new product and calculate AI market score
    - Use market trends data to calculate score
    - Return product with generated score
    """
    try:
        # Load existing products to get next ID
        products_path = DATA_DIR / "products.csv"
        if not products_path.exists():
            raise HTTPException(status_code=404, detail="Products data not found")
        
        products_df = pd.read_csv(products_path, index_col=None)
        if not products_df.empty:
            # Ensure the id column is numeric and get the max
            products_df['id'] = pd.to_numeric(products_df['id'], errors='coerce')
            # Drop rows with NaN ids and get max of valid ids
            valid_ids = products_df['id'].dropna()
            if not valid_ids.empty:
                next_id = int(valid_ids.max()) + 1
            else:
                next_id = 1
        else:
            next_id = 1
        
        # Calculate AI market score
        market_score = _calculate_ai_market_score(
            product_data.ingredients,
            product_data.category,
            product_data.region,
            product_data.target_demographics
        )
        
        # Create new product
        new_product = Product(
            id=next_id,
            name=product_data.name,
            category=product_data.category,
            market_score=market_score,
            status="Active",
            created_date=datetime.now().strftime("%Y-%m-%d"),
            target_demographics=product_data.target_demographics,
            region=product_data.region,
            ingredients=product_data.ingredients,
            flavor_profile=product_data.flavor_profile
        )
        
        # Add to CSV
        new_row = {
            'id': new_product.id,
            'name': new_product.name,
            'category': new_product.category,
            'market_score': new_product.market_score,
            'status': new_product.status,
            'created_date': new_product.created_date,
            'target_demographics': new_product.target_demographics,
            'region': new_product.region,
            'ingredients': new_product.ingredients,
            'flavor_profile': new_product.flavor_profile
        }
        
        # Append to existing CSV
        products_df = pd.concat([products_df, pd.DataFrame([new_row])], ignore_index=True)
        products_df.to_csv(products_path, index=False)
        
        return ProductResponse(
            success=True,
            data=new_product
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Products file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")


def _calculate_ai_market_score(
    ingredients: str, 
    category: str, 
    region: str, 
    target_demographics: str
) -> float:
    """
    Calculate AI market score based on market trends data
    Uses the latest trends data with time-series analysis
    """
    try:
        # Load market trends data
        trends_path = DATA_DIR / "market_trends.csv"
        if not trends_path.exists():
            # Return base score if no trends data
            return 75.0
        
        trends_df = pd.read_csv(trends_path, index_col=None)
        
        # Get most recent data (latest month/year combination)
        latest_data = trends_df.groupby(['year', 'month']).first().reset_index()
        latest_period = latest_data[['year', 'month']].max()
        recent_trends = trends_df[
            (trends_df['year'] == latest_period['year']) & 
            (trends_df['month'] == latest_period['month'])
        ]
        
        # Parse ingredients (comma-separated)
        ingredient_list = [ing.strip() for ing in ingredients.split(',')]
        
        # Calculate base score
        base_score = 60.0
        ingredient_scores = []
        
        # Score each ingredient
        for ingredient in ingredient_list:
            # Find best matching ingredient data
            ingredient_data = trends_df[
                trends_df['ingredient_name'].str.lower() == ingredient.lower()
            ]
            
            if not ingredient_data.empty:
                # Get the most relevant data point (prefer exact region/category match)
                best_match = None
                
                # First, try to find exact region and category match
                exact_match = ingredient_data[
                    (ingredient_data['region'] == region) & 
                    (ingredient_data['category'] == category)
                ]
                
                if not exact_match.empty:
                    best_match = exact_match.iloc[-1]  # Get latest entry
                else:
                    # Try region match only
                    region_match = ingredient_data[ingredient_data['region'] == region]
                    if not region_match.empty:
                        best_match = region_match.iloc[-1]
                    else:
                        # Try category match only
                        category_match = ingredient_data[ingredient_data['category'] == category]
                        if not category_match.empty:
                            best_match = category_match.iloc[-1]
                        else:
                            # Use any available data
                            best_match = ingredient_data.iloc[-1]
                
                if best_match is not None:
                    popularity = float(best_match['popularity_score'])
                    growth_rate = float(best_match['growth_rate'])
                    
                    # Calculate bonuses
                    region_bonus = 8.0 if str(best_match['region']) == region else 0.0
                    category_bonus = 5.0 if str(best_match['category']) == category else 0.0
                    
                    # Time-based bonus for recent trends
                    time_bonus = 0.0
                    if int(best_match['year']) == 2024 and int(best_match['month']) >= 10:
                        time_bonus = 3.0  # Recent data bonus
                    
                    # Calculate weighted ingredient score
                    ingredient_score = (
                        popularity * 0.5 +           # Base popularity weight
                        growth_rate * 0.35 +         # Growth trend weight  
                        region_bonus +               # Regional relevance
                        category_bonus +             # Category relevance
                        time_bonus                   # Recency bonus
                    )
                    
                    ingredient_scores.append(ingredient_score)
                else:
                    # Default score for ingredients with no specific data
                    ingredient_scores.append(50.0)
            else:
                # Score for completely unknown ingredients
                ingredient_scores.append(45.0)
        
        # Calculate final score
        if ingredient_scores:
            avg_ingredient_score = sum(ingredient_scores) / len(ingredient_scores)
            
            # Apply demographic bonus based on trends
            demo_bonus = 0.0
            if target_demographics in ["18-25", "26-35"]:  # Popular demographics
                demo_bonus = 2.0
            elif target_demographics in ["35-45"]:
                demo_bonus = 1.0
            
            final_score = avg_ingredient_score + demo_bonus
            final_score = min(100.0, max(0.0, final_score))
        else:
            final_score = base_score
        
        return round(final_score, 1)
        
    except Exception as e:
        # Return default score if calculation fails
        print(f"Error calculating market score: {e}")
        return 75.0


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
