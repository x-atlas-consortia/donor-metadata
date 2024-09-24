# HuBMAP/SenNet DONOR CLINICAL METADATA UI

import os
import logging
from pathlib import Path
from flask import Flask
import json

# route blueprints
from routes.edit.edit import edit_blueprint
from routes.search.search import search_blueprint
from routes.review.review import review_blueprint

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def to_pretty_json(value):
    # Custom pretty printer of JSON
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))


class DonorUI:

    def __init__(self, config: str, package_base_dir: Path):

        self.app = Flask(__name__,
                         instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'),
                         instance_relative_config=True)

        self.app.package_base_dir = package_base_dir

        # Set secret key for app.
        self.config = config
        self.app.config.from_pyfile(self.config)
        self.app.secret_key = self.app.config['KEY']

        logger.info(f"package_base_dir: {package_base_dir}")

        # Register route Blueprints.
        self.app.register_blueprint(edit_blueprint)
        self.app.register_blueprint(search_blueprint)
        self.app.register_blueprint(review_blueprint)


        # Register the custom JSON pretty print filter.
        self.app.jinja_env.filters['tojson_pretty'] = to_pretty_json

# ###################################################################################################
# For local development/testing
# ###################################################################################################

if __name__ == "__main__":
    try:
        donor_app = DonorUI('./app.cfg', Path(__file__).absolute().parent.parent.parent).app
        donor_app.run(host='0.0.0.0', port='5002')
    except Exception as e:
        print(str(e))
        logger.error(e, exc_info=True)
        print('Error during startup of debug server. Check the log file for further information.')
