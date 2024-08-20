"""
Class for working with information from the Google Sheet of donor clinical metadata valuesets.
"""

import pandas as pd
# For downloading from Google Sheets
import gdown

class ValueSetManager():

    def __init__(self, url:str, download_full_path: str, logger):

        try:
            gdown.download(url, output=download_full_path, fuzzy=True)
            # The spreadsheet has multiple tabs, so sheet_name=None
            self.dfValueset = pd.read_excel(download_full_path,sheet_name=None)
            print(self.dfValueset)
        except FileNotFoundError as e:
            logger.exception('Failed to load the valuesets Google Sheets document.')
            raise e

