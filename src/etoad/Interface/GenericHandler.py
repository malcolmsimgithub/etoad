import logging
from typing import Callable


class GenericHandler(logging.Handler):
    """
    Generic Logging Handler that can be passed any function to serve as the emit method.
    """

    def __init__(self, logging_function: Callable):
        logging.Handler.__init__(self)
        self.logging_function = logging_function

    def flush(self) -> None:
        """
        Defines the flush method of the logging.Handler parent class.
        Does not do anything for the GenericHandler.
        """
        pass

    def emit(self, record: logging.LogRecord) -> None:
        """
        Defines the emit method of the logging.Handler parent class.
        Emits incoming LogRecords through the logging function.

        Args:
            record: incoming LogRecord
        """
        message: str = self.format(record)
        self.logging_function(message)
