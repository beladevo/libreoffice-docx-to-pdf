import logging
import os

def setup_logging(env):
    log_file = os.getenv('LOG_FILE', 'app.log')
    time_log_file = os.getenv('TIME_LOG_FILE', 'conversion_time.log')
    log_level = logging.DEBUG if env == 'development' else logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    time_logger = logging.getLogger('conversion_time')
    time_logger.setLevel(log_level)
    time_logger.addHandler(logging.FileHandler(time_log_file))
