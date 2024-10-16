"""
Class for working with the Flask app.cfg file.
app.cfg files for Flask apps differs from config files formatted for use by the ConfigParser package as follows:
1. Flask configurations lack sections.
2. String values are wrapped in single quotes, which ConfigParser treats as characters.

This class looks for a file named "app.cfg" in the instance directory.

"""
import os
from configparser import ConfigParser
from flask import abort
from pathlib import Path
import logging

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
#logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    #level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
#logger = logging.getLogger(__name__)


class AppConfig:

    # Class to work with the app.cfg file. This file does not contain a section, as expected by ConfigParser.

    def __init__(self):

        # The configuration file contains a number of highly sensitive keys, including those for the
        # Globus clients for both HuBMAP and SenNet. The configuration file is stored outside of the
        # repository, in a subfolder of the user home named 'donor-metadata'.
        home = str(Path('~').expanduser())
        self.path = home + '/donor-metadata'
        self.file = self.path + '/app.cfg'
        self.parser = self.getconfigparser()

    def getconfigparser(self) -> list:

        # The ConfigParser expects a section in the file. Add a section to the read.
        parser = ConfigParser()
        # Set case sensitivity.
        parser.optionxform = str

        try:
            with open(self.file) as stream:
                parser.read_string("[top]\n" + stream.read())

            return parser.items('top')

        except FileNotFoundError as e:
            print(str(e))
            logger.error(e, exc_info=True)
            print(f'Missing configuration file {self.file}.')
            exit(1)

    def getfieldlist(self, prefix: str) -> list:
        """
        Reads from the app.cfg to obtain a list of tuples for use in a WTF SelectField.
        Because this occurs outside the Flask application context, the read of the app.cfg file is separate
        from the app initialization.

        :param prefix: a prefix string that accounts for the lack of a section in Flask configuration files.

        :return: list of tuples in format (key, value)
        """

        listfields = []
        # ConfigParser returns values as tuples, so filter the list.

        for t in self.parser:
            if prefix in t[0]:
                listfields.append(((t[0].replace("'", "")), t[1].replace("'", "")))

        return listfields

    def getfield(self, key: str) -> str:
        """
        Reads from the app.cfg to return a single value.
        :param key: key in the app.cfg file.
        :return: string value, extracted from the tuple obtained from the app.cfg corresponding to the key.
        """
        field = ''
        for t in self.parser:
            if key == t[0]:
                # Trim quotes from tring fields in Flask config files.
                field = t[1].replace("'", "")

        if field == '':
            abort(400, f'Missing key {key} in application configuration file.')

        return field
