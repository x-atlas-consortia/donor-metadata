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
            logging.info('Downloading latest version of valueset file...')
            gdown.download(url, output=download_full_path, fuzzy=True)
            # The spreadsheet has multiple tabs, so sheet_name=None
            self.Sheets = pd.read_excel(download_full_path,sheet_name=None)
        except FileNotFoundError as e:
            logger.exception('Failed to load the valuesets Google Sheets document.')
            raise e

    def getValuesetTuple(self, tab:str, col:str='preferred_term', group_term:str='', list_concepts:list=[], addprompt:bool=False):

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
        :param col: column containing concept labels
        :param group_term: term identifying a subset of rows in the tab with the same value for
                           grouping_concept_preferred_term
        :param list_concepts: optional list of concepts used for "manual" grouping--i.e., not relying on the
                           value of grouping_concept_preferred_term
        NOTE: if group_term takes precedence over list_concepts.
        :param addprompt: flag to indicate whether to add a prompt entry--i.e., "Select an option"
        :return: a list of tuples with values (concept_id, col)
        """
        dfTab = self.Sheets[tab]
        # Optional filters for subset
        if group_term != '':
            dfTab = dfTab.loc[dfTab['grouping_concept_preferred_term']==group_term]
        elif len(list_concepts) > 0:
            dfTab = dfTab.loc[dfTab['concept_id'].isin(list_concepts)]

        dfTab = dfTab.sort_values(by=['preferred_term'])

        # Convert to tuple.
        sTuple = dfTab[['concept_id', col]].apply(tuple, axis=1)

        if addprompt:
            sPrompt = pd.Series([('PROMPT','Select an option')])
            sTuple = pd.concat([sPrompt,sTuple])

        return sTuple


