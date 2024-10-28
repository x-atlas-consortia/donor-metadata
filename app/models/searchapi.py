# Class representing interactions with the search-api for donors

from flask import abort
import requests
import pandas as pd

# Helper class
# Optimizes donor metadata for display in a DataFrame
from .exportmetadata import ExportMetadata


class SearchAPI:

    def __init__(self, token: str, consortium: str):
        """
        :param token: globus groups_token for the consortium's entity-api.
        :param consortium: name of the globus consortium

        """

        if consortium.upper() == 'CONTEXT_HUBMAP':
            self.consortium = 'hubmapconsortium.org'
        else:
            self.consortium = 'sennetconsortium.org'
        self.token = token

        # The url base depends on both the consortium and the enviroment (i.e., development vs production).
        self.urlbase = f'https://search.api.{self.consortium}/'
        if self.consortium == 'hubmapconsortium.org':
            self.urlbase = f'{self.urlbase}/v3/'

        self.headers = {'Authorization': f'Bearer {self.token}'}
        if self.consortium == 'sennetconsortium.org':
            self.headers['X-SenNet-Application'] = 'portal-ui'

        self.metadata = self._getalldonormetadata()

    def _getalldonormetadata(self) -> pd.DataFrame:
        """
        Searches for metadata for donor in a consortium, using the search-api.
        :return: if there is a donor entity with id=donorid, a dict that corresponds to the metadata
        object.
        """
        alldonordf = []
        if self.consortium == 'hubmapconsortium.org':
            entities = 'donors'
        else:
            entities = 'sources'
        url = f'{self.urlbase}param-search/{entities}'

        response = requests.get(url=url, headers=self.headers)

        if response.status_code == 200:

            respjson = response.json()

            for donor in respjson:
                # Obtain a dataframe of flattened metadata for the donor.
                donorexport = ExportMetadata(consortium=self.consortium, donor=donor)
                alldonordf.append(donorexport.dfexport)

            if len(alldonordf) == 0:
                abort(404, f'No human donors found in provenance for {self.consortium }'
                           f' in environment {self.urlbase}')

            # Build a DataFrame for all human donors with metadata in the consortium.
            dfconsortium = pd.concat(alldonordf, ignore_index=True)
            return dfconsortium

        elif response.status_code == 404:
            abort(404, f'No donors found in provenance for {self.consortium} '
                       f'in environment {self.urlbase}')
        elif response.status_code == 400:
            abort(response.status_code, response.json().get('error'))
        else:
            abort(500, 'Error when calling the param-search endpoint in search-api')
