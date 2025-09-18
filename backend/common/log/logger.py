import os
import logging
import logging.config
import inspect


class Logger:
    """
    A logger mixin class that configures and provides a logging instance for views.
    """
    def init_log(self, log_name = None):
        file_name = os.getenv("LOG_FILE_NAME", "backend.log")

        # If no logger name is passed, use the class name
        if not log_name:
            log_name = self.__class__.__name__

        # Create the logging configuration
        # It defines the formatters, handlers, and loggers for the application
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                },
            },
            'handlers': {
                'file': {
                    'level': os.getenv("LOG_LEVEL"),
                    'class': 'logging.FileHandler',
                    'filename': file_name,
                    'formatter': 'default',
                    'encoding': 'utf-8',
                },
                'stdout': {
                    'level': os.getenv("LOG_LEVEL"),   
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                },
            },
            'loggers': {
                log_name: {
                    'handlers': ['file', 'stdout'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
            },
        }

        logging.config.dictConfig(logging_config)
        return logging.getLogger(log_name)

    def __init__(self, log_name=None):
        # Initialize logger with optional custom name
        self.__logger_app = self.init_log(log_name)
    
    def info(self,message):
        self.__logger_app.info(f"{inspect.stack()[1][3]} - {message}")
        
    def warning(self,message):
        self.__logger_app.warning(f"{inspect.stack()[1][3]} - {message}")
    
    def debug(self,message):
        self.__logger_app.debug(f"{inspect.stack()[1][3]} - {message}")
        
    def critical(self,message):
        self.__logger_app.critical(f"{inspect.stack()[1][3]} - {message}")
        
    def error(self,message):
        self.__logger_app.error(f"{inspect.stack()[1][3]} - {message}")
        