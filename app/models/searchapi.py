# Class representing interactions with the search-api for donors.
# Converts a call to the search-api into a DataFrame flattened to the level of individual metadata element, with
# each row including columns for common elements, including donor id.

from flask import abort
import requests
import pandas as pd
from tqdm import tqdm

# For retry loop
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

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
        listdonorid = self.dfalldonormetadata['id'].drop_duplicates().to_list()

        iid = 1
        for id in tqdm(listdonorid, desc="Donors"):
            iid = iid + 1
            if iid == 3:
                break
            # Get the donor.
            donor = self.dfalldonormetadata[self.dfalldonormetadata['id'] == id]
            # Get relevant metadata values.
            age = donor.loc[donor['grouping_concept'] == 'C0001779']['data_value'].values[0]
            sex = donor.loc[donor['grouping_concept'] == 'C1522384']['data_value'].values[0]
            race = donor.loc[donor['grouping_concept'] == 'C0034510']['data_value'].values
            if len(race) == 1:
                race = race[0]
            # Get DOI titles for any published datasets associated with the donor.
            listdatasets = self._getdatasetdoisfordonor(donorid=id)
            for ds in listdatasets:
                listdonor.append({"id": id, "age": age, "sex": sex, "race": race, "doi_url": ds.get('doi_url'), "doi_title": ds.get('doi_title')})

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
            for desc in tqdm(descendants, desc="datasets"):
                # Look for DOIs only for dataset descendants.
                dataset_type = desc.get("dataset_type")
                uuid = desc.get("uuid")
                if dataset_type is not None:
                    source = ["uuid", "doi_url", "registered_doi"]
                    # Get DOI URL
                    donordataset = self._searchmatch(id_field="uuid", id_value=uuid, source=source)
                    if donordataset is not None:
                        doi_url = donordataset.get('hits').get('hits')[0].get('_source').get('doi_url')
                        if doi_url is not None:
                            # Get current DOI title from DataCite.
                            doi_title = self._getdatacitetitle(doi_url=doi_url)
                            listdois.append({"doi_url": doi_url, "doi_title": doi_title})

        return listdois

    def _searchmatch(self, id_field: str, id_value: str, source=None) -> dict:
        """
        Obtain information for an id, using keyword match.
        :param id_field: the field name to match
        :param id_value: the field value to match
        :param source: optional list of specific fields
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

        if source is not None:
            # Limit search results to specified fields.
            data['_source'] = source

        url = f'{self.urlbase}/search'
        #response = (requests.post(url=url, headers=self.headers, json=data))
        return self._getresponsejson(url=url, method='POST', headers=self.headers, json=data)


    def _getdatacitetitle(self, doi_url: str) -> str:
        """
        Queries the DataCite REST API for the title of a DOI.
        """

        doi = doi_url.split('https://doi.org/')[1]
        url = f'https://api.datacite.org/dois/{doi}'
        response = self._getresponsejson(url=url, method='GET')
        if response is not None:
            return response.get("data").get("attributes").get("titles")[0].get("title")

    def _getresponsejson(self, url: str, method: str, headers=None, json=None) -> str:
        """
        Obtains a response from a REST API.
        Employs a retry loop in case of timeout or other failures.

        :param url: the URL to the REST API
        :param method: GET or POST
        :param headers: optional headers
        :param json: optional response body for POST
        :return:
        """

        # Use the HTTPAdapter's retry strategy, as described here:
        # https://oxylabs.io/blog/python-requests-retry

        # Five retries max.
        # A backoff factor of 2, which results in exponential increases in delays before each attempt.
        # Retry for scenarios such as Service Unavailable or Too Many Requests that often are returned in case
        # of an overloaded server.
        try:
            retry = Retry(
                total=5,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504]
            )

            adapter = HTTPAdapter(max_retries=retry)

            session = requests.Session()
            session.mount('https://', adapter)
            # r = session.get('https://httpbin.org/status/502', timeout=180)
            if method == 'GET':
                r = session.get(url=url, timeout=180)
            else:
                r = session.post(url=url, timeout=180, headers=headers, json=json)

            return r.json()

        except Exception as e:
            print('Error with URL', url)
            session.raise_for_status()