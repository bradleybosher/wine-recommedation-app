"""
Debug routes for the Sommelier API.
These endpoints are useful for monitoring, debugging, and diagnostics.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from cache import bust_cache, _conn
from inventory import load_inventory
from profile import load_profile_data

router = APIRouter(prefix="/debug", tags=["debug"])

logger = logging.getLogger("sommelier.api")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics from the database."""
    try:
        with _conn() as c:
            # Get total cache entries
            total = c.execute("SELECT COUNT(*) FROM response_cache").fetchone()[0]
            
            # Get oldest and newest cache entries
            age_result = c.execute(
                "SELECT MIN(created_at), MAX(created_at) FROM response_cache"
            ).fetchone()
            oldest, newest = age_result
            
            # Calculate cache age in hours
            current_time = time.time()
            oldest_age_hours = (current_time - oldest) / 3600 if oldest else 0
            newest_age_hours = (current_time - newest) / 3600 if newest else 0
            
            # Get approximate cache size
            size_result = c.execute(
                "SELECT SUM(LENGTH(response)) FROM response_cache"
            ).fetchone()
            total_size_bytes = size_result[0] or 0
            
            return {
                "total_entries": total,
                "oldest_entry_hours": round(oldest_age_hours, 2) if oldest else None,
                "newest_entry_hours": round(newest_age_hours, 2) if newest else None,
                "total_size_bytes": total_size_bytes,
                "total_size_kb": round(total_size_bytes / 1024, 2) if total_size_bytes else 0,
                "database_path": str(Path(__file__).resolve().parent.parent / "cellar.db")
            }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "error": f"Failed to get cache stats: {str(e)}",
            "total_entries": 0,
            "database_path": str(Path(__file__).resolve().parent.parent / "cellar.db")
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "sommelier-api",
        "version": "1.0.0"
    }


@router.get("/status")
async def status_overview() -> Dict[str, Any]:
    """Comprehensive status overview including system and service metrics."""
    # Get inventory stats
    inv = load_inventory()
    inventory_stats = {
        "has_inventory": bool(inv),
        "bottle_count": len(inv.get("bottles", [])) if inv else 0,
        "age_hours": inv.get("age_hours") if inv else None,
        "stale": inv.get("stale", False) if inv else False
    }
    
    # Get profile stats
    profile_data = load_profile_data()
    profile_stats = {
        "has_profile": bool(profile_data),
        "profile_keys": list(profile_data.keys()) if profile_data else []
    }
    
    # Get cache stats
    cache_stats = get_cache_stats()
    
    # System info
    system_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "working_directory": str(Path.cwd()),
        "environment_variables": {
            "ANTHROPIC_API_KEY_SET": bool(os.getenv("ANTHROPIC_API_KEY")),
            "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        }
    }
    
    return {
        "status": "operational",
        "timestamp": time.time(),
        "inventory": inventory_stats,
        "profile": profile_stats,
        "cache": cache_stats,
        "system": system_info
    }


@router.get("/cache/stats")
async def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return get_cache_stats()


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear all cached responses."""
    bust_cache()
    return {
        "status": "cache_cleared",
        "timestamp": time.time(),
        "message": "All cached responses have been cleared."
    }


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return {
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "anthropic_api_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
    }


@router.get("/logs/recent")
async def get_recent_logs(limit: int = 50) -> Dict[str, Any]:
    """Get recent log entries (last N lines)."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_path = log_dir / "api.log"
    
    if not log_path.exists():
        return {
            "error": "Log file not found",
            "log_path": str(log_path)
        }
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            return {
                "log_file": str(log_path),
                "total_lines": len(lines),
                "recent_lines": recent_lines,
                "limit": limit
            }
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        return {
            "error": f"Failed to read log file: {str(e)}",
            "log_path": str(log_path)
        }


@router.get("/endpoints")
async def list_endpoints(request: Request) -> Dict[str, Any]:
    """List all available API endpoints."""
    routes = []
    for route in request.app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, 'methods') else []
        })
    
    return {
        "endpoints": routes,
        "count": len(routes)
    }


@router.get("/memory")
async def memory_usage() -> Dict[str, Any]:
    """Get memory usage information."""
    try:
        import psutil
        process = psutil.Process()
        
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            "rss_bytes": memory_info.rss,  # Resident Set Size
            "vms_bytes": memory_info.vms,  # Virtual Memory Size
            "percent": memory_percent,
            "available_memory": psutil.virtual_memory().available,
            "total_memory": psutil.virtual_memory().total,
            "psutil_available": True
        }
    except ImportError:
        return {
            "error": "psutil not installed",
            "message": "Install psutil package for memory usage details",
            "psutil_available": False
        }


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Simple ping endpoint for connectivity testing."""
    return {"message": "pong", "timestamp": time.time()}


@router.get("/version")
async def get_version() -> Dict[str, Any]:
    """Get API version information."""
    # Try to read version from requirements or setup files
    version_info = {
        "api": "1.0.0",
        "python": sys.version.split()[0],
        "platform": sys.platform
    }
    
    # Check for pyproject.toml
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        version_info["pyproject_toml"] = True
    
    return version_info