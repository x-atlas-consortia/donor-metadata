"""
Class for working with information from the Google Sheet of donor clinical metadata valuesets.
"""

import pandas as pd
# For downloading from Google Sheets
import gdown
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

class ValueSetManager():

    def __init__(self, url:str, download_full_path: str):

        try:
            logging.info('Loading valuesets...')
            gdown.download(url, output=download_full_path, fuzzy=True)
            # The spreadsheet has multiple tabs, so sheet_name=None
            self.Sheets = pd.read_excel(download_full_path,sheet_name=None)
        except FileNotFoundError as e:
            logger.exception('Failed to load the valuesets Google Sheets document.')
            raise e

    def getValuesetTuple(self, tab:str, col:str='preferred_term', addprompt:bool=False):

        """
        In general, a tab in the ValuesetManager's Google sheet is formatted with columns:

        concept_id
        code
        SAB	data_type
        data_value
        numeric_operator
        units
        preferred_term
        grouping_concept
        grouping_concept_preferred_term
        grouping_code
        grouping_sab

        :param tab: Identifies a tab in the Google Sheets document.
        :return:
        """
        dfTab = self.Sheets[tab]

        sTuple = dfTab[['concept_id', col]].apply(tuple, axis=1)

        if addprompt:
            sPrompt = pd.Series([('PROMPT','Select an option')])
            sTuple = pd.concat([sTuple,sPrompt])

        return sTuple


