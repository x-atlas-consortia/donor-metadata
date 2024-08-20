# HuBMAP/SenNet DONOR CLINICAL METADATA UI

import os
import logging
from flask import Flask
from pathlib import Path

# neo4j connection class
from utils.neo4j_connection_helper import Neo4jConnectionHelper

# valueset data obtained from the Google Sheets document
from classes.valuesetmanager import ValueSetManager

# route blueprints
from routes.index.index_controller import index_blueprint

# Logging configuration
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s', level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class DonorUI:
    # Represents the application.

    def getValuesetManager(self):
        """
        Obtain donor clinical metadata valuesets from the online Google Sheets document
        indicated in the app.cfg file.

        """
        fpath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'valueset')
        download_full_path = os.path.join(fpath, 'valuesets.xslx')
        self.ValuesetManager = ValueSetManager(url=self.app.config['VALUESETMANAGER'],
                                               download_full_path=download_full_path, logger=logger)

    def __init__(self, config, package_base_dir):
        """
        If config is a string then it will be treated as a local file path from which to load a file, e.g.
        app = DonorUI('./app.cfg', package_base_dir).app

        If config is a Flask.config then it will be used directly, e.g.
        config =  Flask(__name__,
                instance_path=path.join(path.abspath(path.dirname(__file__)), 'instance'),
                instance_relative_config=True)\
            .config.from_pyfile('app.cfg')

        The 'package_base_dir' is the base directory of the package (e.g., the directory in which
        the VERSION and BUILD files are located.
        """

        self.app = Flask(__name__,
                         instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'),
                         instance_relative_config=True)

        self.app.package_base_dir = package_base_dir
        logger.info(f"package_base_dir: {package_base_dir}")

        # Register route Blueprints.
        self.app.register_blueprint(index_blueprint)

        self.app.neo4jConnectionHelper = None

        try:
            if Neo4jConnectionHelper.is_initialized():
                self.app.neo4jConnectionHelper = Neo4jConnectionHelper.instance()
                logger.info("Neo4jManager has already been initialized")
            else:
                if isinstance(config, str):
                    logger.info(f'Config provided from file: {config}')
                    self.app.config.from_pyfile(config)
                    self.app.neo4jConnectionHelper = \
                        Neo4jConnectionHelper.create(self.app.config['SERVER'],
                                                     self.app.config['USERNAME'],
                                                     self.app.config['PASSWORD'],
                                                     self.app.config['TIMEOUT'],
                                                     self.app.config['ROWLIMIT'],
                                                     self.app.config['PAYLOADLIMIT'],
                                                     self.app.config['APPCONTEXT'])
                else:
                    logger.info('Using provided Flask config.')
                    # Set self based on passed in config parameters
                    for key, value in config.items():
                        setattr(self, key, value)
                    self.app.neo4jConnectionHelper = \
                        Neo4jConnectionHelper.create(self.SERVER,
                                                     self.USERNAME,
                                                     self.PASSWORD,
                                                     28,
                                                     1000,
                                                     9437184,
                                                     self.APPCONTEXT,
                                                     self.VALUESETMANAGER)
                    logger.info("Initialized Neo4jManager successfully for: {self.SERVER}")
        except Exception as e:
            logger.exception('Failed to initialize the Neo4jManager')
            raise e

        # Get the donor clinical metadata valuesets.
        self.getValuesetManager()

####################################################################################################
## For local development/testing
####################################################################################################

if __name__ == "__main__":
    try:
        donor_app = DonorUI('./app.cfg', Path(__file__).absolute().parent.parent.parent).app
        donor_app.run(host='0.0.0.0', port="5002")
    except Exception as e:
        print("Error during starting debug server.")
        print(str(e))
        logger.error(e, exc_info=True)
        print("Error during startup check the log file for further information")