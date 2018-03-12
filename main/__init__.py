from flask import Flask
import logging
import logging.handlers


def create_app():
    from .views.index import indexblue, mine, new_transaction, full_chain, new_transaction, \
        register_nodes, consensus

    app = Flask(__name__)
    app.register_blueprint(indexblue, url_prefix='/blockchain')
    app.config.from_pyfile('config.py')

    logger_path = app.config.get('LOGGER_PATH')
    logger_format = logging.Formatter(
        '%(asctime)s,%(msecs)03d - %(threadName)s - [%(levelname)s] %(module)s.%(funcName)s:%(lineno)s - %(message)s',
        datefmt='%H:%M:%S')
    handler = logging.handlers.TimedRotatingFileHandler(logger_path, when='D')
    handler.setFormatter(logger_format)
    app.logger.addHandler(handler)

    return app
