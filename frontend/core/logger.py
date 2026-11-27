"""
Logger module providing a mixin class for logging support.

This module provides the Logger base class that can be inherited
by other classes to add logging capabilities.
"""

import logging


class Logger:
    """
    A logger mixin class that configures and provides a logging instance.

    This class uses lazy initialization to create a logger instance
    only when the log property is first accessed. The logger name is
    derived from the class name that inherits from Logger.

    Usage:
        class MyClass(Logger):
            def some_method(self):
                self.log.info("Logging message")

    Attributes:
        log: A logging.Logger instance for the containing class.
    """
    @property
    def log(self):
        """
        Get the logger instance for this class.

        Creates the logger on first access using lazy initialization.
        The logger name is set to the class name that inherits from Logger.

        Returns:
            logging.Logger: Configured logger instance for the class.
        """
        # Create the logger only when accessed (lazy loading)
        if not hasattr(self, '_log'):
            # Use the class name as the logger name
            self._log = logging.getLogger(self.__class__.__name__)
        return self._log
        