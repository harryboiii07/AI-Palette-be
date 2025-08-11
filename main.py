from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uvicorn
import math
from models import Product, ProductCreateRequest, ProductResponse, ProductListResponse, ProductConcept, AnalysisResult, ProductAnalysisResponse

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


@app.get("/api/market-trends")
async def get_market_trends(region: str = None, category: str = None):
    """
    Load market_trends.csv and return trend analysis
    - Filter by region and/or category
    - Return aggregated trend data with popularity scores and growth rates
    - Include time-based analysis showing trends over months
    """
    try:
        # Load market trends CSV
        csv_path = DATA_DIR / "market_trends.csv"
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Market trends data not found")
        
        df = pd.read_csv(csv_path)
        
        # Apply filters
        filtered_df = df.copy()
        
        if region:
            filtered_df = filtered_df[filtered_df['region'].str.lower() == region.lower()]
        
        if category:
            filtered_df = filtered_df[filtered_df['category'].str.lower() == category.lower()]
        
        if filtered_df.empty:
            return {
                "success": True,
                "data": {
                    "trends": [],
                    "summary": {
                        "total_ingredients": 0,
                        "avg_popularity": 0,
                        "avg_growth_rate": 0,
                        "top_ingredients": []
                    },
                    "filters_applied": {
                        "region": region,
                        "category": category
                    }
                }
            }
        
        # Get the latest data for each ingredient
        latest_trends = filtered_df.loc[filtered_df.groupby('ingredient_name')[['year', 'month']].idxmax().values.flatten()]
        
        # Sort by popularity score descending
        latest_trends = latest_trends.sort_values('popularity_score', ascending=False)
        
        # Create trends list
        trends = []
        for _, row in latest_trends.iterrows():
            trend_item = {
                "ingredient_name": row['ingredient_name'],
                "popularity_score": float(row['popularity_score']),
                "growth_rate": float(row['growth_rate']),
                "category": row['category'],
                "region": row['region'],
                "month": int(row['month']),
                "year": int(row['year'])
            }
            trends.append(trend_item)
        
        # Calculate summary statistics
        avg_popularity = float(latest_trends['popularity_score'].mean())
        avg_growth_rate = float(latest_trends['growth_rate'].mean())
        total_ingredients = len(latest_trends)
        
        # Get top 5 ingredients by popularity
        top_ingredients = latest_trends.head(5)[['ingredient_name', 'popularity_score', 'growth_rate']].to_dict('records')
        top_ingredients = [
            {
                "name": item['ingredient_name'],
                "popularity_score": float(item['popularity_score']),
                "growth_rate": float(item['growth_rate'])
            }
            for item in top_ingredients
        ]
        
        # Time series analysis - show trend over months
        time_series = filtered_df.groupby(['year', 'month']).agg({
            'popularity_score': 'mean',
            'growth_rate': 'mean'
        }).reset_index()
        
        time_series_data = []
        for _, row in time_series.iterrows():
            time_series_data.append({
                "year": int(row['year']),
                "month": int(row['month']),
                "avg_popularity": float(row['popularity_score']),
                "avg_growth_rate": float(row['growth_rate'])
            })
        
        return {
            "success": True,
            "data": {
                "trends": trends,
                "summary": {
                    "total_ingredients": total_ingredients,
                    "avg_popularity": round(avg_popularity, 1),
                    "avg_growth_rate": round(avg_growth_rate, 1),
                    "top_ingredients": top_ingredients
                },
                "time_series": time_series_data,
                "filters_applied": {
                    "region": region,
                    "category": category
                }
            }
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Market trends file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing market trends: {str(e)}")


@app.post("/api/analyze-product", response_model=ProductAnalysisResponse)
async def analyze_product(product_concept: ProductConcept):
    """
    Analyze product concept using CSV data
    - Use analysis_results.csv as templates
    - Calculate scores based on ingredients and trends
    - Return comprehensive analysis with recommendations
    """
    try:
        # Load analysis results CSV for template matching
        analysis_path = DATA_DIR / "analysis_results.csv"
        if not analysis_path.exists():
            raise HTTPException(status_code=404, detail="Analysis templates data not found")
        
        # Load analysis results with proper headers
        analysis_df = pd.read_csv(analysis_path, skiprows=1)
        analysis_df.columns = ['analysis_id', 'product_name', 'category', 'overall_score', 'market_demand', 
                              'ingredient_trends', 'competition_level', 'innovation_factor', 'recommendation', 'risk_factor']
        
        # Calculate scores using market trends and analysis templates
        analysis_result = _analyze_product_concept(
            product_concept, 
            analysis_df
        )
        
        return ProductAnalysisResponse(
            success=True,
            data=analysis_result
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Analysis data files not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing product: {str(e)}")


def _analyze_product_concept(concept: ProductConcept, analysis_df: pd.DataFrame) -> AnalysisResult:
    """
    Analyze product concept using existing analysis templates and market data
    """
    try:
        # Load market trends for ingredient analysis
        trends_path = DATA_DIR / "market_trends.csv"
        trends_df = pd.read_csv(trends_path) if trends_path.exists() else pd.DataFrame()
        
        # Calculate base scores using ingredient trends
        ingredient_scores = _calculate_ingredient_scores(concept.ingredients, trends_df, concept.region, concept.category)
        
        # Find similar products in analysis templates for benchmarking
        similar_analyses = _find_similar_analyses(concept, analysis_df)
        
        # Calculate individual score components
        market_demand = _calculate_market_demand_score(concept, ingredient_scores, similar_analyses)
        ingredient_trends_score = ingredient_scores['avg_popularity']
        competition_level = _calculate_competition_score(concept, similar_analyses, analysis_df)
        innovation_factor = _calculate_innovation_score(concept, ingredient_scores, similar_analyses)
        
        # Calculate overall score (weighted average)
        overall_score = round(
            market_demand * 0.25 +
            ingredient_trends_score * 0.25 +
            (100 - competition_level) * 0.20 +  # Lower competition = higher score
            innovation_factor * 0.30, 1
        )
        
        # Generate recommendation and risk assessment
        recommendation = _generate_recommendation(overall_score, market_demand, competition_level, innovation_factor)
        risk_factor = _assess_risk_factors(concept, ingredient_scores, competition_level)
        
        # Create detailed breakdown
        analysis_breakdown = {
            "ingredient_analysis": {
                "total_ingredients": ingredient_scores['total_ingredients'],
                "trending_ingredients": ingredient_scores['trending_count'],
                "avg_growth_rate": ingredient_scores['avg_growth_rate'],
                "regional_match": ingredient_scores['regional_matches'],
                "category_match": ingredient_scores['category_matches']
            },
            "market_positioning": {
                "category_saturation": _get_category_saturation(concept.category, analysis_df),
                "similar_products_count": len(similar_analyses),
                "differentiation_potential": innovation_factor
            },
            "score_weights": {
                "market_demand": "25%",
                "ingredient_trends": "25%", 
                "competition_impact": "20%",
                "innovation_factor": "30%"
            }
        }
        
        return AnalysisResult(
            overall_score=overall_score,
            market_demand=round(market_demand, 1),
            ingredient_trends=round(ingredient_trends_score, 1),
            competition_level=round(competition_level, 1),
            innovation_factor=round(innovation_factor, 1),
            recommendation=recommendation,
            risk_factor=risk_factor,
            analysis_breakdown=analysis_breakdown
        )
        
    except Exception as e:
        # Return default analysis if calculation fails
        print(f"Error in product analysis: {e}")
        return AnalysisResult(
            overall_score=75.0,
            market_demand=75.0,
            ingredient_trends=70.0,
            competition_level=80.0,
            innovation_factor=75.0,
            recommendation="Moderate market potential. Consider market research for validation.",
            risk_factor="Standard market risks apply. Monitor ingredient availability.",
            analysis_breakdown={"note": "Analysis based on default scoring due to data limitations"}
        )


def _calculate_ingredient_scores(ingredients: str, trends_df: pd.DataFrame, region: str, category: str) -> Dict[str, float]:
    """Calculate scores based on ingredient trends"""
    ingredient_list = [ing.strip() for ing in ingredients.split(',')]
    
    if trends_df.empty:
        return {
            'avg_popularity': 70.0,
            'avg_growth_rate': 5.0,
            'trending_count': 0,
            'total_ingredients': len(ingredient_list),
            'regional_matches': 0,
            'category_matches': 0
        }
    
    scores = []
    growth_rates = []
    trending_count = 0
    regional_matches = 0
    category_matches = 0
    
    for ingredient in ingredient_list:
        ingredient_data = trends_df[trends_df['ingredient_name'].str.lower() == ingredient.lower()]
        
        if not ingredient_data.empty:
            # Get the best matching data point
            best_match = None
            
            # Prefer region + category match
            exact_match = ingredient_data[
                (ingredient_data['region'] == region) & 
                (ingredient_data['category'] == category)
            ]
            
            if not exact_match.empty:
                best_match = exact_match.iloc[-1]
                regional_matches += 1
                category_matches += 1
            else:
                # Try region match
                region_match = ingredient_data[ingredient_data['region'] == region]
                if not region_match.empty:
                    best_match = region_match.iloc[-1]
                    regional_matches += 1
                else:
                    # Try category match
                    category_match = ingredient_data[ingredient_data['category'] == category]
                    if not category_match.empty:
                        best_match = category_match.iloc[-1]
                        category_matches += 1
                    else:
                        # Use any available data
                        best_match = ingredient_data.iloc[-1]
            
            if best_match is not None:
                popularity = float(best_match['popularity_score'])
                growth_rate = float(best_match['growth_rate'])
                
                scores.append(popularity)
                growth_rates.append(growth_rate)
                
                # Count as trending if popularity > 80 and growth > 10%
                if popularity > 80 and growth_rate > 10:
                    trending_count += 1
        else:
            # Default score for unknown ingredients
            scores.append(60.0)
            growth_rates.append(5.0)
    
    return {
        'avg_popularity': sum(scores) / len(scores) if scores else 60.0,
        'avg_growth_rate': sum(growth_rates) / len(growth_rates) if growth_rates else 5.0,
        'trending_count': trending_count,
        'total_ingredients': len(ingredient_list),
        'regional_matches': regional_matches,
        'category_matches': category_matches
    }


def _find_similar_analyses(concept: ProductConcept, analysis_df: pd.DataFrame) -> pd.DataFrame:
    """Find similar product analyses for benchmarking"""
    # Filter by category first
    category_matches = analysis_df[analysis_df['category'] == concept.category]
    
    if not category_matches.empty:
        return category_matches
    
    # If no category matches, find products with similar ingredients
    ingredient_keywords = [ing.strip().lower() for ing in concept.ingredients.split(',')[:3]]  # Top 3 ingredients
    
    similar_products = []
    for _, row in analysis_df.iterrows():
        product_name_lower = row['product_name'].lower()
        if any(keyword in product_name_lower for keyword in ingredient_keywords):
            similar_products.append(row)
    
    return pd.DataFrame(similar_products) if similar_products else analysis_df.head(10)


def _calculate_market_demand_score(concept: ProductConcept, ingredient_scores: Dict, similar_analyses: pd.DataFrame) -> float:
    """Calculate market demand score"""
    base_score = ingredient_scores['avg_popularity']
    
    # Bonus for trending ingredients
    trending_bonus = min(10.0, ingredient_scores['trending_count'] * 3.0)
    
    # Regional/category match bonus
    match_bonus = (ingredient_scores['regional_matches'] + ingredient_scores['category_matches']) * 2.0
    
    # Similar products average (if available)
    similar_avg = 75.0
    if not similar_analyses.empty and 'market_demand' in similar_analyses.columns:
        similar_avg = similar_analyses['market_demand'].mean()
    
    # Weighted combination
    demand_score = (base_score * 0.4) + (similar_avg * 0.4) + trending_bonus + match_bonus
    
    return min(100.0, max(0.0, demand_score))


def _calculate_competition_score(concept: ProductConcept, similar_analyses: pd.DataFrame, analysis_df: pd.DataFrame) -> float:
    """Calculate competition level (higher = more competitive)"""
    # Base competition from category saturation
    category_count = len(analysis_df[analysis_df['category'] == concept.category])
    total_count = len(analysis_df)
    category_saturation = (category_count / total_count) * 100 if total_count > 0 else 50.0
    
    # Similar products competition
    similar_count = len(similar_analyses)
    similarity_competition = min(50.0, similar_count * 2.0)
    
    # Average competition from similar products
    similar_competition_avg = 80.0
    if not similar_analyses.empty and 'competition_level' in similar_analyses.columns:
        similar_competition_avg = similar_analyses['competition_level'].mean()
    
    # Weighted competition score
    competition_score = (category_saturation * 0.3) + (similarity_competition * 0.3) + (similar_competition_avg * 0.4)
    
    return min(100.0, max(0.0, competition_score))


def _calculate_innovation_score(concept: ProductConcept, ingredient_scores: Dict, similar_analyses: pd.DataFrame) -> float:
    """Calculate innovation factor score"""
    base_innovation = 70.0
    
    # Bonus for high-growth ingredients
    growth_bonus = min(15.0, ingredient_scores['avg_growth_rate'])
    
    # Bonus for trending ingredients
    trending_bonus = ingredient_scores['trending_count'] * 5.0
    
    # Uniqueness bonus (fewer similar products = more innovative)
    uniqueness_bonus = max(0.0, 10.0 - len(similar_analyses))
    
    # Penalty for very common categories
    category_penalty = 0.0
    if len(similar_analyses) > 15:
        category_penalty = 5.0
    
    innovation_score = base_innovation + growth_bonus + trending_bonus + uniqueness_bonus - category_penalty
    
    return min(100.0, max(0.0, innovation_score))


def _generate_recommendation(overall_score: float, market_demand: float, competition_level: float, innovation_factor: float) -> str:
    """Generate recommendation based on scores"""
    if overall_score >= 85:
        return "Excellent market opportunity with strong potential for success. Recommend immediate development."
    elif overall_score >= 75:
        if competition_level > 85:
            return "Good market potential but high competition. Focus on differentiation strategy."
        else:
            return "Strong market opportunity with manageable competition. Proceed with development."
    elif overall_score >= 65:
        if innovation_factor < 70:
            return "Moderate potential. Consider reformulation with more trending ingredients."
        else:
            return "Decent opportunity with innovation potential. Conduct market testing."
    else:
        return "Limited market potential. Significant reformulation or repositioning recommended."


def _assess_risk_factors(concept: ProductConcept, ingredient_scores: Dict, competition_level: float) -> str:
    """Assess primary risk factors"""
    risks = []
    
    if ingredient_scores['trending_count'] == 0:
        risks.append("Limited trending ingredients")
    
    if competition_level > 85:
        risks.append("High market competition")
    
    if ingredient_scores['regional_matches'] == 0:
        risks.append("Limited regional ingredient preference data")
    
    if ingredient_scores['avg_growth_rate'] < 5:
        risks.append("Low ingredient growth trends")
    
    if len(risks) == 0:
        return "Standard market risks. Monitor ingredient availability and consumer trends."
    elif len(risks) <= 2:
        return f"Moderate risks: {', '.join(risks)}. Mitigation strategies recommended."
    else:
        return f"High risks: {', '.join(risks)}. Comprehensive risk management required."


def _get_category_saturation(category: str, analysis_df: pd.DataFrame) -> str:
    """Get category saturation level"""
    category_count = len(analysis_df[analysis_df['category'] == category])
    total_count = len(analysis_df)
    
    saturation_pct = (category_count / total_count) * 100 if total_count > 0 else 0
    
    if saturation_pct > 25:
        return "High"
    elif saturation_pct > 15:
        return "Medium"
    else:
        return "Low"


@app.get("/api/competitors")
async def get_competitors(category: str = None):
    """
    Load competitors.csv and return market analysis
    - Filter by primary category (optional)
    - Return competitor analysis with market insights
    - Include market share distribution and competitive positioning
    """
    try:
        # Load competitors CSV
        csv_path = DATA_DIR / "competitors.csv"
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Competitors data not found")
        
        df = pd.read_csv(csv_path)
        
        # Apply category filter if provided
        filtered_df = df.copy()
        if category:
            filtered_df = filtered_df[filtered_df['primary_category'].str.lower() == category.lower()]
        
        if filtered_df.empty:
            return {
                "success": True,
                "data": {
                    "competitors": [],
                    "market_analysis": {
                        "total_competitors": 0,
                        "total_market_share": 0.0,
                        "average_score": 0.0,
                        "average_growth": 0.0,
                        "market_leaders": [],
                        "emerging_players": []
                    },
                    "category_breakdown": {},
                    "regional_analysis": {},
                    "filters_applied": {
                        "category": category
                    }
                }
            }
        
        # Sort by market share descending
        sorted_df = filtered_df.sort_values('market_share', ascending=False)
        
        # Create competitors list
        competitors = []
        for _, row in sorted_df.iterrows():
            competitor = {
                "id": int(row['id']),
                "company_name": row['company_name'],
                "total_products": int(row['total_products']),
                "average_score": float(row['average_score']),
                "market_share": float(row['market_share']),
                "growth_trend": float(row['growth_trend']),
                "primary_category": row['primary_category'],
                "region": row['region'],
                "founded_year": int(row['founded_year']),
                "market_position": _calculate_market_position(
                    float(row['market_share']), 
                    float(row['average_score']), 
                    float(row['growth_trend'])
                )
            }
            competitors.append(competitor)
        
        # Calculate market analysis
        total_competitors = len(filtered_df)
        total_market_share = float(filtered_df['market_share'].sum())
        average_score = float(filtered_df['average_score'].mean())
        average_growth = float(filtered_df['growth_trend'].mean())
        
        # Identify market leaders (top 20% by market share)
        top_20_percent = max(1, int(len(sorted_df) * 0.2))
        market_leaders = []
        for _, row in sorted_df.head(top_20_percent).iterrows():
            market_leaders.append({
                "company_name": row['company_name'],
                "market_share": float(row['market_share']),
                "average_score": float(row['average_score']),
                "growth_trend": float(row['growth_trend'])
            })
        
        # Identify emerging players (high growth, founded recently)
        emerging_players = []
        recent_companies = filtered_df[filtered_df['founded_year'] >= 2020]
        high_growth_recent = recent_companies[recent_companies['growth_trend'] > average_growth]
        for _, row in high_growth_recent.sort_values('growth_trend', ascending=False).head(5).iterrows():
            emerging_players.append({
                "company_name": row['company_name'],
                "growth_trend": float(row['growth_trend']),
                "founded_year": int(row['founded_year']),
                "market_share": float(row['market_share'])
            })
        
        # Category breakdown (if no category filter applied)
        category_breakdown = {}
        if not category:
            category_stats = df.groupby('primary_category').agg({
                'market_share': 'sum',
                'average_score': 'mean',
                'growth_trend': 'mean',
                'company_name': 'count'
            }).round(2)
            
            for cat, stats in category_stats.iterrows():
                category_breakdown[cat] = {
                    "total_market_share": float(stats['market_share']),
                    "average_score": float(stats['average_score']),
                    "average_growth": float(stats['growth_trend']),
                    "competitor_count": int(stats['company_name'])
                }
        
        # Regional analysis
        regional_stats = filtered_df.groupby('region').agg({
            'market_share': 'sum',
            'average_score': 'mean',
            'growth_trend': 'mean',
            'company_name': 'count'
        }).round(2)
        
        regional_analysis = {}
        for region, stats in regional_stats.iterrows():
            regional_analysis[region] = {
                "total_market_share": float(stats['market_share']),
                "average_score": float(stats['average_score']),
                "average_growth": float(stats['growth_trend']),
                "competitor_count": int(stats['company_name'])
            }
        
        market_analysis = {
            "total_competitors": total_competitors,
            "total_market_share": round(total_market_share, 1),
            "average_score": round(average_score, 1),
            "average_growth": round(average_growth, 1),
            "market_leaders": market_leaders,
            "emerging_players": emerging_players
        }
        
        return {
            "success": True,
            "data": {
                "competitors": competitors,
                "market_analysis": market_analysis,
                "category_breakdown": category_breakdown,
                "regional_analysis": regional_analysis,
                "filters_applied": {
                    "category": category
                }
            }
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Competitors file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing competitors: {str(e)}")


def _calculate_market_position(market_share: float, average_score: float, growth_trend: float) -> str:
    """
    Calculate market position based on market share, score, and growth
    """
    # Normalize scores for comparison
    # High market share (>15%), high score (>85), high growth (>8%)
    
    if market_share > 15.0 and average_score > 85.0:
        return "Market Leader"
    elif growth_trend > 10.0 and average_score > 80.0:
        return "Rising Star"
    elif market_share > 10.0:
        return "Established Player"
    elif growth_trend > 8.0:
        return "Emerging Competitor"
    elif average_score > 85.0:
        return "Quality Focused"
    else:
        return "Niche Player"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
