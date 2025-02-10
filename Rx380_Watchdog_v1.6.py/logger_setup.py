import logging

def setup_logger(config):
    level = getattr(logging, config.get("level", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        filename=config.get("log_file", "app.log"),
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    # Also log to console:
    console = logging.StreamHandler()
    console.setLevel(level)
    logging.getLogger('').addHandler(console)
    return logging.getLogger()
