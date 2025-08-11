from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class DashboardMetricsResponse(BaseModel):
    """Response model for dashboard metrics"""
    success: bool
    data: Dict[str, Any]


class GrowthMetrics(BaseModel):
    """Growth metrics data model"""
    products_growth: float
    success_rate_growth: float
    users_growth: float


class DashboardData(BaseModel):
    """Dashboard data model"""
    total_products: int
    success_rate: float
    active_users: int
    trending_categories: int
    growth_metrics: GrowthMetrics


class Product(BaseModel):
    """Product data model"""
    id: Optional[int] = None
    name: str
    category: str
    market_score: float
    status: str = "Active"
    created_date: Optional[str] = None
    target_demographics: str
    region: str
    ingredients: str
    flavor_profile: str


class ProductCreateRequest(BaseModel):
    """Request model for creating a product"""
    name: str
    category: str
    target_demographics: str
    region: str
    ingredients: str
    flavor_profile: str


class ProductResponse(BaseModel):
    """Response model for single product"""
    success: bool
    data: Product


class ProductListResponse(BaseModel):
    """Response model for product list"""
    success: bool
    data: List[Product]
    pagination: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class ProductConcept(BaseModel):
    """Product concept for analysis"""
    name: str
    category: str
    ingredients: str
    target_demographics: str
    region: str
    flavor_profile: Optional[str] = None
    description: Optional[str] = None


class AnalysisResult(BaseModel):
    """Analysis result data model"""
    overall_score: float
    market_demand: float
    ingredient_trends: float
    competition_level: float
    innovation_factor: float
    recommendation: str
    risk_factor: str
    analysis_breakdown: Dict[str, Any]


class ProductAnalysisResponse(BaseModel):
    """Response model for product analysis"""
    success: bool
    data: AnalysisResult
