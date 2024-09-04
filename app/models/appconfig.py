"""
Class for working with the Flask app.cfg file.
app.cfg files for Flask apps differs from config files formatted for use by the ConfigParser package
in that Flask configurations lack sections.
"""
import os
from configparser import ConfigParser


class AppConfig:

    # Class to work with the app.cfg file. This file does not contain a section, as expected by ConfigParser.

    def __init__(self):
        self.parser = self.getconfigparser()

    def getconfigparser(self) -> list:

        # Read from the app.cfg file.
        fpath = os.path.dirname(os.getcwd())
        fpath = os.path.join(fpath, 'app/instance/app.cfg')

        # The ConfigParser expects a section in the file. Add a section to the read.
        parser = ConfigParser()
        # Set case sensitivity.
        parser.optionxform = str

        with open(fpath) as stream:
            parser.read_string("[top]\n" + stream.read())

        return parser.items('top')

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
                listfields.append(((t[0].replace("'", "")),t[1].replace("'", "")))

        return listfields

    def getfield(self, key: str) -> str:
        """
        Reads from the app.cfg to return a single value.
        :param key: key in the app.cfg file.
        :return: string value, extracted from the tuple obtained from the app.cfg corresponding to the key.
        """
        for t in self.parser:
            if key == t[0]:
                return t[1]
