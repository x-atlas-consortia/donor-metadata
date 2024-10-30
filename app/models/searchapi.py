# Class representing interactions with the search-api for donors.
# Converts a call to the search-api into a DataFrame flattened to the level of individual metadata element, with
# each row including columns for common elements, including donor id.

from flask import abort
import requests
import pandas as pd

# Helper classes
# Optimizes donor metadata for display in a DataFrame
from .metadataframe import MetadataFrame

from .getmetadatabytype import getmetadatabytype

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

        self.dfalldonormetata = self._getalldonormetadata()

    def _getalldonormetadata(self) -> pd.DataFrame:
        """
        Searches for metadata for donor in a consortium, using the search-api.
        :return: if there is a donor entity with id=donorid, a DataFrame with flattened donor metadata.
        """
        listalldonordf = []

        # HuBMAP entity-api uses donors; SenNet entity-api uses sources.
        if self.consortium == 'hubmapconsortium.org':
            entities = 'donors'
        else:
            entities = 'sources'
        url = f'{self.urlbase}param-search/{entities}'

        response = requests.get(url=url, headers=self.headers)

        if response.status_code == 200:

            respjson = response.json()

            for donorjson in respjson:

                # Only return metadata for human sources in SenNet.
                if self.consortium == 'sennetconsortium.org':
                    source_type = donorjson.get('source_type')
                    donorid = donorjson.get('sennet_id')
                    getdonor = source_type == 'Human'
                else:
                    getdonor = True
                    donorid = donorjson.get('hubmap_id')

                if getdonor:
                    dictmetadata = donorjson.get('metadata')
                    if dictmetadata is not None and dictmetadata!={}:
                        metadata = getmetadatabytype(dictmetadata=dictmetadata)
                        donorexport = MetadataFrame(metadata=metadata, donorid=donorid)
                        listalldonordf.append(donorexport.dfexport)

            if len(listalldonordf) == 0:
                abort(404, f'No human donors found in provenance for {self.consortium }'
                           f' in environment {self.urlbase}')

            # Build a DataFrame for all human donors with metadata in the consortium.
            dfconsortium = pd.concat(listalldonordf, ignore_index=True)
            return dfconsortium

        elif response.status_code == 404:
            abort(404, f'No donors found in provenance for {self.consortium} '
                       f'in environment {self.urlbase}')
        elif response.status_code == 400:
            abort(response.status_code, response.json().get('error'))
        else:
            abort(500, 'Error when calling the param-search endpoint in search-api')
