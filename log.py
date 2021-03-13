import logging

def setup_custom_logger(name, loglevel):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(loglevel)
    logger.addHandler(handler)

    fh = logging.FileHandler('results.log')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    return logger

setup_custom_logger('root', logging.DEBUG)