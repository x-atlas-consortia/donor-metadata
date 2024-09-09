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


class ValueSetManager:

    def __init__(self, url: str, download_full_path: str):

        try:
            logging.info('Downloading latest version of valueset file...')
            gdown.download(url, output=download_full_path, fuzzy=True)
            # The spreadsheet has multiple tabs, so sheet_name=None
            self.Sheets = pd.read_excel(download_full_path, sheet_name=None)
        except FileNotFoundError as e:
            logger.exception('Failed to load the valuesets Google Sheets document.')
            raise e

    def getvaluesettuple(self, tab: str, col: str = 'preferred_term', group_term: str = None,
                         list_concepts: list = None,
                         addprompt: bool = False) -> list:

        """
        Translates a valueset into a list of tuples. The list of tuples will be provided as the choices parameter
        for a WTForms SelectField.

        In general, a tab in the ValuesetManager's Google sheet is formatted with the following columns:

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

        :param tab: Identifies a tab in the Google Sheets document corresponding to a valueset.
        :param col: column containing concept labels
        :param group_term: term identifying a subset of rows in the tab that share a value for
                           grouping_concept_preferred_term
                           NOTE: group_term is used instead of grouping_concept to account for the case in
                           which a subset does not share a grouping_concept. This is currently the case for
                           the Fitzgerald Scale in Measurements.
        :param list_concepts: optional list of concepts used for "manual" grouping--i.e., not relying on the
                           value of grouping_concept_preferred_term. This is often the case for a set of rows
                           in a general tab such as Measurments or Social History.
        NOTE: group_term takes precedence over list_concepts.
        :param addprompt: flag to indicate whether to add a prompt entry--i.e., "Select an option"
        :return: a list of tuples with values (concept_id, col)
        """

        # Obtain relevant valueset.
        dftab = self.Sheets[tab]

        # Apply filters for subset.
        if group_term is not None:
            dftab = dftab.loc[dftab['grouping_concept_preferred_term'] == group_term]
        elif len(list_concepts) > 0:
            dftab = dftab.loc[dftab['concept_id'].isin(list_concepts)]

        # Sort and filter to relevant columns.
        dftab = dftab.sort_values(by=['preferred_term'])[['concept_id', col]]

        if addprompt:
            # Append a prompt row.
            # NOTE: The prompt must be the last row in the dataset. This is apparently a bug in the WTForms
            # SelectField: if the prompt is the first row, it cannot be selected programmatically. No idea why.
            data = {'concept_id': ['PROMPT'], 'preferred_term': ['Select an option']}
            dfprompt = pd.DataFrame(data=data)
            dftab = pd.concat([dftab, dfprompt], ignore_index=True)

        # Convert to tuple.
        stuple = dftab[['concept_id', col]].apply(tuple, axis=1)
        return stuple

    def getcolumnvalues(self, tab: str, col: str) -> list:
        """
        Returns values in the specified column of a tab of the valueset sheet.
        :param tab: Identifies a tab in the Google Sheets document.
        :param col: column name
        :return: list of values
        """
        dftab = self.Sheets[tab]
        return dftab[col].drop_duplicates().to_list()
