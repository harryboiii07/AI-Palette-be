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
