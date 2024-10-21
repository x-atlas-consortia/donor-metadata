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
            self.consoritum = 'sennetconsortium.org'
        self.token = token

        # The url base depends on both the consortium and the enviroment (i.e., development vs production).
        self.urlbase = f'https://search.api.{self.consortium}/v3/'
        #self.headers = {'Accept': 'application/json',
                        #'Content-Type': 'application/json'}

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
        listrow= []
        url = self.urlbase + 'param-search/donors'
        response = requests.get(url=url, headers=self.headers)

        if response.status_code == 200:

            respjson = response.json()

            dfconsortium = pd.DataFrame()

            for donor in respjson:

                donor_metadata = donor.get('metadata')
                if donor_metadata is not None:
                    if 'organ_donor_data' in donor_metadata.keys():
                        source_name = 'organ_donor_data'
                    else:
                        source_name = 'living_donor_data'
                    if self.consortium == 'hubmapconsortium.org':
                        id = donor['hubmap_id']
                    else:
                        id = donor['sennet_id']

                    metadata = donor_metadata[source_name]
                    for m in metadata:
                        # Flatten each metadata element for a donor into a row that includes the donor id and
                        # source name.
                        mnew={}
                        mnew['id'] = id
                        mnew['source_name'] = source_name
                        for key in m:
                            mnew[key] = m[key]

                        # Create the metadata element into a DataFrame, wrapping the dict in a list.
                        dfdonor = pd.DataFrame([mnew])
                        listrow.append(dfdonor)

            # Build a DataFrame for all donors in the consortium.
            dfconsortium = pd.concat(listrow, ignore_index=True)
            return dfconsortium

        elif response.status_code == 404:
            abort(404, f'No donors found in provenance for {self.consortium} '
                       f'in environment {self.urlbase}')
        elif response.status_code == 400:
            abort(response.status_code, response.json().get('error'))


