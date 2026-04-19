"""
ASGI entry point for Render deployment
This wrapper properly handles module imports from the project root
"""
import sys
import logging
from pathlib import Path

# Configure logging to catch startup issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Add backend directory to Python path BEFORE any imports
    backend_path = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_path))
    logger.info(f"Added to sys.path: {backend_path}")
    
    # Now import the app
    from app.main import app
    logger.info("✓ Successfully imported FastAPI app")
    
    # This makes the app available for uvicorn
    __all__ = ["app"]
    
except Exception as e:
    logger.error(f"✗ Failed to import app: {str(e)}", exc_info=True)
    raise
