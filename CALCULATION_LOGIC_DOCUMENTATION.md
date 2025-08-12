# FlavorForge API - Complete Calculation Logic Documentation

## Table of Contents
1. [AI Market Scoring Algorithm](#ai-market-scoring-algorithm)
2. [Product Analysis Engine](#product-analysis-engine)
3. [Market Trends Analytics](#market-trends-analytics)
4. [Dashboard Metrics Calculation](#dashboard-metrics-calculation)
5. [Competitive Analysis Logic](#competitive-analysis-logic)
6. [Similar Products Detection](#similar-products-detection)
7. [Data Processing Utilities](#data-processing-utilities)

---

## **1. AI Market Scoring Algorithm**

### **Function: `_calculate_ai_market_score()`**

**Purpose**: Calculate market viability score (0-100) for new products based on ingredient trends and market data.

### **Input Parameters**
- `ingredients` (string): Comma-separated ingredient list
- `category` (string): Product category (Beverages, Snacks, etc.)
- `region` (string): Target market region
- `target_demographics` (string): Target age group

### **Algorithm Flow**

#### **Step 1: Data Preparation**
```python
# Load market trends data
trends_df = pd.read_csv("market_trends.csv")

# Parse ingredients
ingredient_list = [ing.strip() for ing in ingredients.split(',')]

# Initialize scoring variables
base_score = 60.0
ingredient_scores = []
```

#### **Step 2: Ingredient Matching Logic**

For each ingredient, find the best matching market data using **priority hierarchy**:

```python
def find_best_match(ingredient, trends_df, region, category):
    ingredient_data = trends_df[trends_df['ingredient_name'].str.lower() == ingredient.lower()]
    
    # Priority 1: Exact region + category match
    exact_match = ingredient_data[
        (ingredient_data['region'] == region) & 
        (ingredient_data['category'] == category)
    ]
    if not exact_match.empty:
        return exact_match.iloc[-1]  # Most recent entry
    
    # Priority 2: Region-only match
    region_match = ingredient_data[ingredient_data['region'] == region]
    if not region_match.empty:
        return region_match.iloc[-1]
    
    # Priority 3: Category-only match
    category_match = ingredient_data[ingredient_data['category'] == category]
    if not category_match.empty:
        return category_match.iloc[-1]
    
    # Priority 4: Any available data
    if not ingredient_data.empty:
        return ingredient_data.iloc[-1]
    
    return None  # No data found
```

#### **Step 3: Individual Ingredient Scoring**

```python
def calculate_ingredient_score(best_match, region, category):
    if best_match is None:
        return 45.0  # Default score for unknown ingredients
    
    # Extract base metrics
    popularity = float(best_match['popularity_score'])
    growth_rate = float(best_match['growth_rate'])
    
    # Calculate bonuses
    region_bonus = 8.0 if str(best_match['region']) == region else 0.0
    category_bonus = 5.0 if str(best_match['category']) == category else 0.0
    
    # Time-based bonus (for recent data)
    time_bonus = 0.0
    if int(best_match['year']) == 2024 and int(best_match['month']) >= 10:
        time_bonus = 3.0
    
    # Weighted calculation
    ingredient_score = (
        popularity * 0.5 +      # 50% weight on popularity
        growth_rate * 0.35 +    # 35% weight on growth rate
        region_bonus +          # Regional relevance bonus
        category_bonus +        # Category relevance bonus
        time_bonus              # Recency bonus
    )
    
    return ingredient_score
```

#### **Step 4: Final Score Calculation**

```python
def calculate_final_score(ingredient_scores, target_demographics):
    if not ingredient_scores:
        return 75.0  # Default fallback score
    
    # Average ingredient scores
    avg_ingredient_score = sum(ingredient_scores) / len(ingredient_scores)
    
    # Demographic bonus
    demo_bonus = 0.0
    if target_demographics in ["18-25", "26-35"]:
        demo_bonus = 2.0
    elif target_demographics == "35-45":
        demo_bonus = 1.0
    
    # Final calculation
    final_score = avg_ingredient_score + demo_bonus
    
    # Normalize to 0-100 range
    return round(min(100.0, max(0.0, final_score)), 1)
```

### **Scoring Weights Summary**
| Component | Weight | Maximum Points |
|-----------|--------|---------------|
| Popularity Score | 50% | Variable |
| Growth Rate | 35% | Variable |
| Region Match | Fixed | 8 points |
| Category Match | Fixed | 5 points |
| Recency Bonus | Fixed | 3 points |
| Demographics | Fixed | 2 points |

### **Example Calculation**
```python
# Input: Matcha, Asia Pacific, Beverages
popularity = 94, growth_rate = 21.2
score = (94 * 0.5) + (21.2 * 0.35) + 8 + 5 + 3 = 70.42 points
```

---

## **2. Product Analysis Engine**

### **Function: `_analyze_product_concept()`**

**Purpose**: Comprehensive AI analysis using multiple data sources and weighted scoring system.

### **Multi-Component Scoring System**

#### **Overall Score Calculation**
```python
overall_score = (
    market_demand * 0.25 +           # 25% weight
    ingredient_trends * 0.25 +       # 25% weight
    (100 - competition_level) * 0.20 + # 20% weight (inverted)
    innovation_factor * 0.30         # 30% weight
)
```

### **Component 1: Market Demand Score**

#### **Function: `_calculate_market_demand_score()`**
```python
def calculate_market_demand(concept, ingredient_scores, similar_analyses):
    # Base score from ingredient popularity
    base_score = ingredient_scores['avg_popularity']
    
    # Trending ingredients bonus (max 10 points)
    trending_bonus = min(10.0, ingredient_scores['trending_count'] * 3.0)
    
    # Regional/category match bonus (2 points each)
    match_bonus = (
        ingredient_scores['regional_matches'] + 
        ingredient_scores['category_matches']
    ) * 2.0
    
    # Historical performance from similar products
    similar_avg = 75.0  # Default
    if not similar_analyses.empty and 'market_demand' in similar_analyses.columns:
        similar_avg = similar_analyses['market_demand'].mean()
    
    # Weighted combination
    demand_score = (
        base_score * 0.4 +      # 40% current ingredient trends
        similar_avg * 0.4 +     # 40% historical performance
        trending_bonus +        # Trending bonus
        match_bonus             # Relevance bonus
    )
    
    return min(100.0, max(0.0, demand_score))
```

### **Component 2: Ingredient Trends Score**

#### **Function: `_calculate_ingredient_scores()`**
```python
def calculate_ingredient_scores(ingredients, trends_df, region, category):
    ingredient_list = [ing.strip() for ing in ingredients.split(',')]
    
    scores = []
    growth_rates = []
    trending_count = 0
    regional_matches = 0
    category_matches = 0
    
    for ingredient in ingredient_list:
        # Find best matching data (using priority system)
        best_match = find_best_ingredient_match(ingredient, trends_df, region, category)
        
        if best_match is not None:
            popularity = float(best_match['popularity_score'])
            growth_rate = float(best_match['growth_rate'])
            
            scores.append(popularity)
            growth_rates.append(growth_rate)
            
            # Count trending ingredients (popularity > 80 AND growth > 10%)
            if popularity > 80 and growth_rate > 10:
                trending_count += 1
            
            # Count matches
            if best_match['region'] == region:
                regional_matches += 1
            if best_match['category'] == category:
                category_matches += 1
        else:
            # Default scores for unknown ingredients
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
```

### **Component 3: Competition Level Score**

#### **Function: `_calculate_competition_score()`**
```python
def calculate_competition(concept, similar_analyses, analysis_df):
    # Category saturation analysis
    category_count = len(analysis_df[analysis_df['category'] == concept.category])
    total_count = len(analysis_df)
    category_saturation = (category_count / total_count) * 100 if total_count > 0 else 50.0
    
    # Similar products competition intensity
    similar_count = len(similar_analyses)
    similarity_competition = min(50.0, similar_count * 2.0)
    
    # Historical competition data from similar products
    similar_competition_avg = 80.0  # Default
    if not similar_analyses.empty and 'competition_level' in similar_analyses.columns:
        similar_competition_avg = similar_analyses['competition_level'].mean()
    
    # Weighted competition score
    competition_score = (
        category_saturation * 0.3 +      # 30% market saturation
        similarity_competition * 0.3 +   # 30% direct competition
        similar_competition_avg * 0.4    # 40% historical data
    )
    
    return min(100.0, max(0.0, competition_score))
```

### **Component 4: Innovation Factor Score**

#### **Function: `_calculate_innovation_score()`**
```python
def calculate_innovation(concept, ingredient_scores, similar_analyses):
    base_innovation = 70.0
    
    # High-growth ingredients bonus (max 15 points)
    growth_bonus = min(15.0, ingredient_scores['avg_growth_rate'])
    
    # Trending ingredients bonus (5 points each)
    trending_bonus = ingredient_scores['trending_count'] * 5.0
    
    # Market uniqueness bonus (fewer similar products = more innovative)
    uniqueness_bonus = max(0.0, 10.0 - len(similar_analyses))
    
    # Penalty for oversaturated categories
    category_penalty = 5.0 if len(similar_analyses) > 15 else 0.0
    
    innovation_score = (
        base_innovation + 
        growth_bonus + 
        trending_bonus + 
        uniqueness_bonus - 
        category_penalty
    )
    
    return min(100.0, max(0.0, innovation_score))
```

---

## **3. Market Trends Analytics**

### **Function: `get_market_trends()`**

#### **Data Processing Logic**
```python
def process_market_trends(df, region=None, category=None):
    # Apply filters
    filtered_df = df.copy()
    
    if region:
        filtered_df = filtered_df[filtered_df['region'].str.lower() == region.lower()]
    
    if category:
        filtered_df = filtered_df[filtered_df['category'].str.lower() == category.lower()]
    
    # Get latest data for each ingredient
    latest_trends = filtered_df.loc[
        filtered_df.groupby('ingredient_name')[['year', 'month']].idxmax().values.flatten()
    ]
    
    # Sort by popularity (descending)
    latest_trends = latest_trends.sort_values('popularity_score', ascending=False)
    
    return latest_trends
```

#### **Summary Statistics Calculation**
```python
def calculate_trend_summary(latest_trends):
    # Basic statistics
    avg_popularity = float(latest_trends['popularity_score'].mean())
    avg_growth_rate = float(latest_trends['growth_rate'].mean())
    total_ingredients = len(latest_trends)
    
    # Top 5 ingredients by popularity
    top_ingredients = latest_trends.head(5)[
        ['ingredient_name', 'popularity_score', 'growth_rate']
    ].to_dict('records')
    
    return {
        "total_ingredients": total_ingredients,
        "avg_popularity": round(avg_popularity, 1),
        "avg_growth_rate": round(avg_growth_rate, 1),
        "top_ingredients": top_ingredients
    }
```

#### **Time Series Analysis**
```python
def generate_time_series(filtered_df):
    # Group by time period and calculate averages
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
    
    return time_series_data
```

---

## **4. Dashboard Metrics Calculation**

### **Function: `_calculate_dashboard_metrics()`**

#### **Metric Extraction Logic**
```python
def extract_metrics(df):
    def get_metric_value(metric_name, default_value=0.0):
        metric_row = df[df['metric_name'] == metric_name]
        if not metric_row.empty:
            return float(metric_row['metric_value'].iloc[0])
        return default_value
    
    def get_growth_percentage(metric_name, default_value=0.0):
        metric_row = df[df['metric_name'] == metric_name]
        if not metric_row.empty:
            return float(metric_row['growth_percentage'].iloc[0])
        return default_value
    
    # Extract core metrics
    metrics = {
        "total_products": int(get_metric_value('total_products', 247)),
        "success_rate": get_metric_value('success_rate', 87.5),
        "active_users": int(get_metric_value('active_users', 1432)),
        "trending_categories": int(get_metric_value('trending_categories', 5))
    }
    
    # Extract growth metrics
    growth_metrics = {
        "products_growth": get_growth_percentage('total_products', 12.3),
        "success_rate_growth": get_growth_percentage('success_rate', 3.2),
        "users_growth": get_growth_percentage('active_users', 8.1)
    }
    
    return metrics, growth_metrics
```

---

## **5. Competitive Analysis Logic**

### **Market Position Classification**

#### **Function: `_calculate_market_position()`**
```python
def calculate_market_position(market_share, average_score, growth_trend):
    """
    Multi-factor market position classification
    """
    # High-performance leaders
    if market_share > 15.0 and average_score > 85.0:
        return "Market Leader"
    
    # High-growth performers
    elif growth_trend > 10.0 and average_score > 80.0:
        return "Rising Star"
    
    # Established market presence
    elif market_share > 10.0:
        return "Established Player"
    
    # Growth-focused companies
    elif growth_trend > 8.0:
        return "Emerging Competitor"
    
    # Quality-focused niche
    elif average_score > 85.0:
        return "Quality Focused"
    
    # Default classification
    else:
        return "Niche Player"
```

#### **Market Leaders Identification**
```python
def identify_market_leaders(sorted_df):
    # Top 20% by market share
    top_20_percent = max(1, int(len(sorted_df) * 0.2))
    market_leaders = []
    
    for _, row in sorted_df.head(top_20_percent).iterrows():
        market_leaders.append({
            "company_name": row['company_name'],
            "market_share": float(row['market_share']),
            "average_score": float(row['average_score']),
            "growth_trend": float(row['growth_trend'])
        })
    
    return market_leaders
```

#### **Emerging Players Detection**
```python
def identify_emerging_players(filtered_df):
    # Recent companies with high growth
    recent_companies = filtered_df[filtered_df['founded_year'] >= 2020]
    average_growth = filtered_df['growth_trend'].mean()
    
    emerging_players = []
    high_growth_recent = recent_companies[
        recent_companies['growth_trend'] > average_growth
    ]
    
    for _, row in high_growth_recent.sort_values('growth_trend', ascending=False).head(5).iterrows():
        emerging_players.append({
            "company_name": row['company_name'],
            "growth_trend": float(row['growth_trend']),
            "founded_year": int(row['founded_year']),
            "market_share": float(row['market_share'])
        })
    
    return emerging_players
```

---

## **6. Similar Products Detection**

### **Function: `_find_similar_analyses()`**

#### **Two-Tier Matching Strategy**
```python
def find_similar_analyses(concept, analysis_df):
    # Tier 1: Category-based matching (primary)
    category_matches = analysis_df[analysis_df['category'] == concept.category]
    
    if not category_matches.empty:
        return category_matches
    
    # Tier 2: Ingredient-based matching (fallback)
    ingredient_keywords = [
        ing.strip().lower() 
        for ing in concept.ingredients.split(',')[:3]  # First 3 ingredients
    ]
    
    similar_products = []
    for _, row in analysis_df.iterrows():
        product_name_lower = row['product_name'].lower()
        
        # Check if any ingredient keyword appears in product name
        if any(keyword in product_name_lower for keyword in ingredient_keywords):
            similar_products.append(row)
    
    if similar_products:
        return pd.DataFrame(similar_products)
    
    # Tier 3: Default fallback
    return analysis_df.head(10)
```

#### **Matching Priority Explanation**

**Tier 1: Category-Based Matching**
- **Purpose**: Find direct competitors in same product category
- **Logic**: Products in same category compete for same market space
- **Example**: All "Beverages" products compete with each other

**Tier 2: Ingredient-Based Matching**
- **Purpose**: Find products with similar ingredients when category matches fail
- **Logic**: Similar ingredients appeal to similar consumer preferences
- **Example**: Products containing "matcha" appeal to health-conscious consumers

**Tier 3: Default Fallback**
- **Purpose**: Provide baseline comparison when no specific matches found
- **Logic**: Use general market data for broad benchmarking

---

## **7. Data Processing Utilities**

### **Timeframe Parsing**
```python
def _parse_timeframe(timeframe):
    """Convert timeframe string to days"""
    timeframe_map = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }
    return timeframe_map.get(timeframe, 30)
```

### **Category Saturation Analysis**
```python
def _get_category_saturation(category, analysis_df):
    """Calculate market saturation level"""
    category_count = len(analysis_df[analysis_df['category'] == category])
    total_count = len(analysis_df)
    
    saturation_pct = (category_count / total_count) * 100 if total_count > 0 else 0
    
    if saturation_pct > 25:
        return "High"
    elif saturation_pct > 15:
        return "Medium"
    else:
        return "Low"
```

### **Recommendation Engine**
```python
def _generate_recommendation(overall_score, market_demand, competition_level, innovation_factor):
    """Generate business recommendations based on analysis scores"""
    
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
```

### **Risk Assessment Logic**
```python
def _assess_risk_factors(concept, ingredient_scores, competition_level):
    """Identify and prioritize risk factors"""
    risks = []
    
    # Check for various risk conditions
    if ingredient_scores['trending_count'] == 0:
        risks.append("Limited trending ingredients")
    
    if competition_level > 85:
        risks.append("High market competition")
    
    if ingredient_scores['regional_matches'] == 0:
        risks.append("Limited regional ingredient preference data")
    
    if ingredient_scores['avg_growth_rate'] < 5:
        risks.append("Low ingredient growth trends")
    
    # Generate risk assessment
    if len(risks) == 0:
        return "Standard market risks. Monitor ingredient availability and consumer trends."
    elif len(risks) <= 2:
        return f"Moderate risks: {', '.join(risks)}. Mitigation strategies recommended."
    else:
        return f"High risks: {', '.join(risks)}. Comprehensive risk management required."
```

---

## **Calculation Summary Tables**

### **AI Market Scoring Weights**
| Component | Weight | Description |
|-----------|--------|-------------|
| Popularity Score | 50% | Current market appeal |
| Growth Rate | 35% | Trend momentum |
| Region Match | 8 pts | Geographic relevance |
| Category Match | 5 pts | Product type relevance |
| Time Bonus | 3 pts | Data recency |
| Demographics | 2 pts | Target audience bonus |

### **Product Analysis Weights**
| Component | Weight | Focus Area |
|-----------|--------|------------|
| Innovation Factor | 30% | Market differentiation |
| Market Demand | 25% | Consumer appeal |
| Ingredient Trends | 25% | Trend alignment |
| Competition Impact | 20% | Market saturation |

### **Market Position Classifications**
| Position | Criteria |
|----------|----------|
| Market Leader | Market Share > 15% AND Score > 85% |
| Rising Star | Growth > 10% AND Score > 80% |
| Established Player | Market Share > 10% |
| Emerging Competitor | Growth > 8% |
| Quality Focused | Score > 85% |
| Niche Player | Default classification |

### **Risk Factor Thresholds**
| Risk Factor | Threshold | Impact |
|-------------|-----------|--------|
| Limited Trending Ingredients | trending_count = 0 | Moderate |
| High Market Competition | competition_level > 85 | High |
| Limited Regional Data | regional_matches = 0 | Moderate |
| Low Growth Trends | avg_growth_rate < 5 | Moderate |

### **Data Source Requirements**
| API Endpoint | Required CSV Files | Key Columns |
|--------------|-------------------|-------------|
| Market Scoring | market_trends.csv | ingredient_name, popularity_score, growth_rate |
| Product Analysis | analysis_results.csv, market_trends.csv | All analysis columns |
| Market Trends | market_trends.csv | All trend columns |
| Dashboard | dashboard_metrics.csv | metric_name, metric_value, growth_percentage |
| Competitors | competitors.csv | company_name, market_share, average_score |

### **Example Calculations**

#### **AI Market Scoring Example**
```
Product: "Golden Turmeric Matcha Latte"
Ingredients: Turmeric (89 popularity, 17.3% growth), Matcha (89, 16.8%), Coconut Milk (77, 12.2%)

Turmeric Score = (89 * 0.5) + (17.3 * 0.35) + 8 + 5 + 3 = 66.55
Matcha Score = (89 * 0.5) + (16.8 * 0.35) + 8 + 0 + 3 = 56.38
Coconut Score = (77 * 0.5) + (12.2 * 0.35) + 0 + 5 + 3 = 46.77

Average = (66.55 + 56.38 + 46.77) / 3 = 56.57
Final Score = 56.57 + 2 (demographic bonus) = 58.6
```

#### **Product Analysis Example**
```
Overall Score Calculation:
- Market Demand: 84.0 (25% weight) = 21.0 points
- Ingredient Trends: 85.0 (25% weight) = 21.25 points  
- Competition Impact: (100 - 41.6) * 20% = 11.68 points
- Innovation Factor: 100.0 (30% weight) = 30.0 points

Total Overall Score = 21.0 + 21.25 + 11.68 + 30.0 = 83.93
```

---

## **Error Handling & Edge Cases**

### **Data Missing Scenarios**
1. **Missing CSV Files**: Returns default scores with appropriate error messages
2. **Missing Ingredients**: Uses default scores (45.0 for unknown ingredients)
3. **No Similar Products**: Falls back to default analysis templates
4. **Invalid Data Types**: Handles conversion errors gracefully

### **Default Values**
| Scenario | Default Value | Reasoning |
|----------|---------------|-----------|
| Unknown Ingredient | 45.0 | Conservative estimate |
| Missing Market Data | 75.0 | Neutral market score |
| No Similar Products | Top 10 from dataset | Broad benchmarking |
| Missing Demographics | 0.0 bonus | No demographic advantage |

This documentation provides the complete mathematical and logical foundation for all calculation algorithms used in the FlavorForge API system.
