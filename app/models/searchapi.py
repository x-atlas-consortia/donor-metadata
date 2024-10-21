# Class representing interactions with the search-api for donors

from flask import abort
import requests
import pandas as pd


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

        self.metadata = self.getalldonormetadata()

    def getalldonormetadata(self) -> pd.DataFrame:
        """
        Searches for metadata for donor in a consortium, using the search-api.
        :return: if there is a donor entity with id=donorid, a dict that corresponds to the metadata
        object.
        """
        listrow = []
        if self.consortium == 'hubmapconsortium.org':
            entities = 'donors'
        else:
            entities = 'sources'
        url = f'{self.urlbase}param-search/{entities}'

        response = requests.get(url=url, headers=self.headers)

        if response.status_code == 200:

            respjson = response.json()

            for donor in respjson:

                # Only return metadata for human sources in SenNet.
                if self.consortium == 'sennetconsortium.org':
                    entity_type = donor['source_type']
                    getdonor = entity_type == 'Human'
                else:
                    getdonor = True

                if getdonor:
                    donor_metadata = donor.get('metadata')
                    # Metadata is keyed differently based on whether the donor was living or an organ donor.
                    if donor_metadata is not None:
                        if 'organ_donor_data' in donor_metadata.keys():
                            source_name = 'organ_donor_data'
                        else:
                            source_name = 'living_donor_data'

                        # ID key is based on consortium.
                        if self.consortium == 'hubmapconsortium.org':
                            donorid = donor['hubmap_id']
                        else:
                            donorid = donor['sennet_id']

                        metadata = donor_metadata.get(source_name)
                        if metadata is not None:
                            for m in metadata:
                                # Flatten each metadata element for a donor into a row that includes the donor id and
                                # source name. Order columns.
                                mnew = {}
                                mnew['id'] = donorid
                                mnew['source_name'] = source_name
                                for key in m:
                                    mnew[key] = m[key]

                                # Create the metadata element into a DataFrame, wrapping the dict in a list.
                                dfdonor = pd.DataFrame([mnew])
                                listrow.append(dfdonor)

            if len(listrow) == 0:
                abort(404, f'No human donors found in provenance for {self.consortium }'
                           f' in environment {self.urlbase}')

            # Build a DataFrame for all human donors with metadata in the consortium.
            dfconsortium = pd.concat(listrow, ignore_index=True)
            return dfconsortium

        elif response.status_code == 404:
            abort(404, f'No donors found in provenance for {self.consortium} '
                       f'in environment {self.urlbase}')
        elif response.status_code == 400:
            abort(response.status_code, response.json().get('error'))
        else:
            abort(500,'Error when calling the param-search endpoint in search-api')
