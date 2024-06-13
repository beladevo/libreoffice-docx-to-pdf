import logging
import logging.config
import os

def setup_logging(env='development'):
    log_file = os.getenv('LOG_FILE', 'app.log')
    time_log_file = os.getenv('TIME_LOG_FILE', 'conversion_time.log')

    if env == 'production':
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
            },
            'handlers': {
                'file': {
                    'level': 'INFO',
                    'formatter': 'standard',
                    'class': 'logging.FileHandler',
                    'filename': log_file,
                },
            },
            'root': {
                'handlers': ['file'],
                'level': 'INFO',
            },
        })
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    time_logger = logging.getLogger('conversion_time')
    time_logger.setLevel(logging.INFO)

    time_handler = logging.FileHandler(time_log_file)
    time_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    time_logger.addHandler(time_handler)
