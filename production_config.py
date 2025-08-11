"""
Production configuration for FlavorForge API
"""
import os
from pathlib import Path

# Production settings
ENVIRONMENT = "production"
DEBUG = False

# Server configuration
HOST = "0.0.0.0"
PORT = 8000
WORKERS = 4

# CORS settings for production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com",  # Replace with your frontend domain
    # Add more allowed origins as needed
]

# Security settings
ALLOWED_HOSTS = ["*"]  # Configure this properly for production

# Logging configuration
LOGGING_LEVEL = "INFO"
LOG_FILE = "/var/log/flavorforge-api.log"

# Data directory
DATA_DIR = Path("/var/www/flavorforge-api/data")

# API configuration
API_TITLE = "FlavorForge API"
API_DESCRIPTION = "AI-powered product development platform for FMCG companies"
API_VERSION = "1.0.0"

# Rate limiting (if implemented)
RATE_LIMIT_PER_MINUTE = 100

# Database settings (if you add a database later)
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flavorforge.db")

# Cache settings (if you add caching later)
# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Monitoring and health checks
HEALTH_CHECK_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"
