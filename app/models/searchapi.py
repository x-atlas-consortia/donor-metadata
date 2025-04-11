# Class representing interactions with the search-api for donors.
# Converts a call to the search-api into a DataFrame flattened to the level of individual metadata element, with
# each row including columns for common elements, including donor id.

import time

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

        # April 2025 - Remove default search of data for all donors data.
        #self.dfalldonormetadata = self.getalldonormetadata()

    def getalldonormetadata(self) -> pd.DataFrame:
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

    def getalldonordoimetadata(self, start: int, end: int) -> pd.DataFrame:
        """
        April 2025
        Extracts from the dfalldonormetadata DataFrame metadata relevant to
        DOIs for published datasets.
        :param start: ordinal number of first donor in a batch to process.
        :param end: ordinal number of the last donor in a batch to process.
    """
        listdonor = []
        # Get a sorted list of donor ids.
        listdonorid = self.dfalldonormetadata['id'].drop_duplicates().to_list()
        listdonorid.sort()
        if start > len(listdonorid):
            start = len(listdonorid) - 1
            end = start

        for donorid in tqdm(listdonorid[start:end], desc="Donors"):

            # Get the donor.
            donor = self.dfalldonormetadata[self.dfalldonormetadata['id'] == donorid]
            # Get relevant metadata values.
            age = donor.loc[donor['grouping_concept'] == 'C0001779']['data_value'].values[0]
            sex = donor.loc[donor['grouping_concept'] == 'C1522384']['data_value'].values[0]
            race = donor.loc[donor['grouping_concept'] == 'C0034510']['data_value'].values
            if len(race) == 1:
                race = race[0]
            # Get DOI titles for any published datasets associated with the donor.
            listdatasets = self.getdatasetdoisfordonor(donorid=donorid)
            if len(listdatasets) == 0:
                listdonor.append({"id": donorid, "age": age, "sex": sex, "race": race, "doi_url": "no published datasets",
                                  "doi_title": "no published datasets"})
            else:
                for ds in listdatasets:
                    listdonor.append({"id": donorid, "age": age, "sex": sex, "race": race, "doi_url": ds.get('doi_url'),
                                      "doi_title": ds.get('doi_title')})

            time.sleep(10)

        return pd.DataFrame(listdonor)

    def getdatasetdoisfordonor(self, donorid: str) -> list:
        """
        Obtains DOI information on published datasets of a donor.
        :param donorid: HuBMAP or SenNet ID of the donor.

        """

        # Get set of published datasets of the donor entity.
        if self.consortium == 'hubmapconsortium.org':
            return self._gethubmapdoisfordonor(donorid=donorid)
        else:
            return self._getsennetdoisfordonor(donorid=donorid)

    def _gethubmapdoisfordonor(self, donorid: str) -> list:
        """
            Obtains DOI information on published datasets of a HuBMAP donor.
            :param donorid: HuBMAP ID of the donor.
        """

        listdois = []

        # In HuBMAP, datasets are in the descendants array of the donor entity.
        id_field = 'hubmap_id'
        dictdonor = self._searchmatch(id_field=id_field, id_value=donorid)
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

    def _getsennetdoisfordonor(self, donorid: str) -> list:
        """
            Obtains DOI information on published datasets of a SenNet donor.
            :param donorid: SenNet ID of the donor.
        """
        listdois = []

        # In SenNet, donor entities do not have links to datasets; instead, datasets
        # have links to a source.
        id_field = 'source.sennet_id'
        source = ["uuid", "doi_url", "registered_doi"]
        dictdonor = self._searchmatch(id_field=id_field, id_value=donorid, source=source)

        descendants = dictdonor.get('hits').get('hits')
        #for desc in tqdm(descendants, desc="datasets"):
        for desc in descendants:
            # Look for DOIs for published datasets.
            source = desc.get("_source")
            doi_url = source.get("doi_url")
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
        # response = (requests.post(url=url, headers=self.headers, json=data))
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

    def _getresponsejson(self, url: str, method: str, headers=None, json=None) -> dict:
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
                total=10,
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
            print(f'Error with URL {url}, json={json}: {e}')
            abort(500)
