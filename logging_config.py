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
                'time_file': {
                    'level': 'INFO',
                    'formatter': 'standard',
                    'class': 'logging.FileHandler',
                    'filename': time_log_file,
                },
            },
            'loggers': {
                '': {
                    'handlers': ['file'],
                    'level': 'INFO',
                },
                'conversion_time': {
                    'handlers': ['time_file'],
                    'level': 'INFO',
                    'propagate': False
                },
            }
        })
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    time_logger = logging.getLogger('conversion_time')
    time_logger.setLevel(logging.INFO)

    if env != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

        root_logger = logging.getLogger('')
        if not any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
            root_logger.addHandler(console_handler)

        if not any(isinstance(handler, logging.StreamHandler) for handler in time_logger.handlers):
            time_logger.addHandler(console_handler)

    if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == time_log_file for handler in time_logger.handlers):
        time_handler = logging.FileHandler(time_log_file)
        time_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        time_logger.addHandler(time_handler)

    if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file for handler in logging.getLogger('').handlers):
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        logging.getLogger('').addHandler(file_handler)
