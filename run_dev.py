import os
import logging
from logging.handlers import RotatingFileHandler
from app import app, db

# Development environment configuration
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'
os.environ['DATABASE_URI'] = 'sqlite:///rfms_xtracr_dev.db'

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler(
            "app_dev.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting RFMS PDF XTRACR in development mode")
logger.debug("Debug logging enabled")

# Ensure upload directory exists
os.makedirs('uploads', exist_ok=True)

# Initialize development database
with app.app_context():
    db.create_all()
    logger.info("Development database initialized successfully")

if __name__ == '__main__':
    # Run development server
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    ) 