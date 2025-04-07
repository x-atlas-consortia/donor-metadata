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
            self.urlbase = f'{self.urlbase}v3/'

        self.headers = {'Authorization': f'Bearer {self.token}'}
        if self.consortium == 'sennetconsortium.org':
            self.headers['X-SenNet-Application'] = 'portal-ui'

        self.dfalldonormetadata = self._getalldonormetadata()

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
                    if dictmetadata is not None and dictmetadata != {}:
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

    def getalldonordoimetadata(self) -> pd.DataFrame:
        """
        Extracts from the dfalldonormetadata DataFrame metadata relevant to
        DOIs for published datasets.
    """
        listdonor = []
        sdonorid = self.dfalldonormetadata['id'].drop_duplicates().to_list()

        for id in sdonorid:

            # Get the donor.
            donor = self.dfalldonormetadata[self.dfalldonormetadata['id'] == id]
            # Get relevant metadata values.
            age = donor.loc[donor['grouping_concept'] == 'C0001779']['data_value'].values[0]
            sex = donor.loc[donor['grouping_concept'] == 'C1522384']['data_value'].values[0]
            race = donor.loc[donor['grouping_concept'] == 'C0034510']['data_value'].values
            if len(race) == 1:
                race = race[0]

            listdatasets = self._getdatasetdoisfordonor(donorid=id)
            for ds in listdatasets:
                listdonor.append({"id": id, "age": age, "sex": sex, "race": race, "doi_url": ds.get('doi_url'), "doi_title": ds.get('doi_title')})
            # Get the IDs for datasets for donor.

        return pd.DataFrame(listdonor)

    def _getdatasetdoisfordonor(self, donorid: str) -> list:
        """
        Obtains DOI information on published datasets of a donor.
        :param donorid: HuBMAP or SenNet ID of the donor.

        """
        listdois = []

        if self.consortium == 'hubmapconsortium.org':
            id_field = 'hubmap_id'
        else:
            id_field = 'sennet_id'
        dictdonor = self._searchmatch(id_field=id_field, id_value=donorid)

        # Get descendants of the donor entity.
        descendants = dictdonor.get('hits').get('hits')[0].get('_source').get('descendants')
        if descendants is not None:
            for desc in descendants:
                dataset_type = desc.get("dataset_type")
                uuid = desc.get("uuid")
                if dataset_type is not None:
                    donordataset = self._searchmatch(id_field="uuid", id_value=uuid)
                    if donordataset is not None:
                        doi_url = donordataset.get('hits').get('hits')[0].get('_source').get('doi_url')
                        if doi_url is not None:
                            doi_title = self._getdatacitetitle(doi_url=doi_url)
                            listdois.append({"doi_url": doi_url, "doi_title": doi_title})

        return listdois

    def _searchmatch(self, id_field: str, id_value: str) -> dict:
        """
        Obtain information for an id, using keyword match.
        :param id_field: the field name to match
        :param id_value: the field value to match
        :return: dict for results of the search API.

        """
        listret = []

        data = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match_phrase": {
                                id_field: id_value
                            }
                        }
                    ]
                }
            }
        }

        url = f'{self.urlbase}/search'
        response = requests.post(url=url, headers=self.headers, json=data)

        if response.status_code == 200:
            return response.json()

    def _getdatacitetitle(self, doi_url: str) -> str:
        """
        Queries the DataCite REST API for the title of a DOI.
        """

        doi = doi_url.split('https://doi.org/')[1]
        url = f'https://api.datacite.org/dois/{doi}'
        response = requests.get(url=url)
        if response.status_code == 200:
            respjson = response.json()
            return respjson.get("data").get("attributes").get("titles")[0].get("title")