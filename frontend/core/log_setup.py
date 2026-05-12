"""
Logging configuration for the Stamps web application.

This module sets up the application's logging system with:
- File handler using RotatingFileHandler (5MB max, 5 backups)
- Colored console handler for development debugging
- Separate log levels for different modules (root, watchfiles, uvicorn, etc.)

The configuration uses dictionary-based logging config for flexibility.
"""

import logging
import logging.config
from pathlib import Path

from settings import LOG_BASE_DIR, LOG_FILE_NAME, LOG_LEVEL


def log_setup() -> None:
    """Configure logging with file and console handlers.
    
    Sets up the logging system with:
    - File output to LOG_BASE_DIR/LOG_FILE_NAME (rotates at 5MB, keeps 5 backups)
    - Colored console output for DEBUG/INFO/WARNING/ERROR/CRITICAL levels
    - Suppressed verbose logs from third-party libraries (flet, uvicorn, etc.)
    
    Returns:
        None: This function configures logging in-place.
    """
    # Ensure the log directory exists
    log_path = Path(LOG_FILE_NAME)
    if not log_path.is_absolute():
        log_path = Path(LOG_BASE_DIR) / log_path
        
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    color_scheme = {
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] - %(name)s - %(funcName)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'colored_console': {
                '()': 'colorlog.ColoredFormatter', # Use the colorlog class
                'format': '%(log_color)s%(asctime)s [%(levelname)s] - %(name)s - %(funcName)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'log_colors': color_scheme,
            },
        },
        'handlers': {
            'file': {
                'level': LOG_LEVEL,
                # Use RotatingFileHandler to prevent disk fill-up
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_path),
                'maxBytes': 1024 * 1024 * 5, # 5 MB
                'backupCount': 5,            # Keep 5 backup files
                'formatter': 'standard',
                'encoding': 'utf-8',
            },
            'console': {
                'level': LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'colored_console',
            },
        },
        'loggers': {
            # The root logger catches everything
            '': { 
                'handlers': ['file', 'console'],
                'level': LOG_LEVEL,
                'propagate': True,
            },
            'watchfiles': {
                'handlers': ['console'], # Optional: Keep it in console if you want, remove 'file'
                'level': 'WARNING',      # Only show warnings/errors, hide DEBUG changes
                'propagate': False,      # Stop it from bubbling up to the root logger
            },
            # You might also want to silence uvicorn access logs if they are too noisy
            'uvicorn.access': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            # urllib3
            'urllib3': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            # asyncio
            'asyncio': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            # Flet framework - suppress debug messages
            'flet': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'flet_core': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'flet_transport': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'flet_controls': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'flet_web': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
        }
    }

    logging.config.dictConfig(logging_config)