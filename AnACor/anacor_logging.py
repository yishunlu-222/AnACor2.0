import json

import logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "time": self.formatTime(record, self.datefmt)
        }
        return json.dumps(log_record)

def setup_logger(filename='./logging.log'):
    logger = logging.getLogger('json_logger')

    # Check if the logger already has handlers
    if not logger.handlers:
        # Create a file handler that logs to a JSON file
        file_handler = logging.FileHandler(filename, mode="w", delay=True)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

        # Create a console handler that logs to the console
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


class ColorFormatter(logging.Formatter):
    COLORS = {
        'WARNING': '\033[93m',  # Yellow
        'INFO': '\033[92m',     # Green
        'DEBUG': '\033[94m',    # Blue
        'CRITICAL': '\033[91m', # Red
        'ERROR': '\033[91m',    # Red
        'RESET': '\033[0m',     # Reset
    }

    def format(self, record):
        log_fmt = f'{self.COLORS[record.levelname]}{self._fmt}{self.COLORS["RESET"]}'
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger('colored_logger')
logger.setLevel(logging.DEBUG)

# Create a console handler and use the color formatter
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(ColorFormatter('%(levelname)s: %(message)s'))

# Add the handler to the logger
logger.addHandler(ch)