import logging

def configure_logging(level=logging.INFO):
    """Centralized logging configuration for the application.
    This sets a basic handler only if no handlers are present so imports from
    libraries or repeated calls don't reconfigure logging.
    """
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    root.setLevel(level)

def get_logger(name: str):
    return logging.getLogger(name)
