# Class representing interactions with the search-api for donors.
# Converts a call to the search-api into a DataFrame flattened to the level of individual metadata element, with
# each row including columns for common elements, including donor id.

import time
import os
import sys

from flask import abort
import requests
import pandas as pd
from tqdm import tqdm

# Helper classes
# Optimizes donor metadata for display in a DataFrame
# April 2025. Because this file is used by both the donor-metadata app and scripts in the
# validate path, set relative paths to parent package.
fpath = os.path.dirname(os.getcwd())
fpath = os.path.join(fpath, 'app/models')
sys.path.append(fpath)
from metadataframe import MetadataFrame
from getmetadatabytype import getmetadatabytype
from getresponsejson import getresponsejson
# to obtain DOI information for published datasets
from datacite import DataCiteAPI

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

        # The url base depends on both the consortium and the environment (i.e., development vs production).
        self.urlbase = f'https://search.api.{self.consortium}/'
        if self.consortium == 'hubmapconsortium.org':
            self.urlbase = f'{self.urlbase}v3/'

        self.headers = {'Authorization': f'Bearer {self.token}'}
        if self.consortium == 'sennetconsortium.org':
            self.headers['X-SenNet-Application'] = 'portal-ui'

        # April 2025 - class to integrate DOI information.
        self.datacite = DataCiteAPI(consortium=self.consortium)


    def getalldonormetadata(self) -> pd.DataFrame:
        """
        Searches for metadata for donor in a consortium, using the search-api.
        :return: a DataFrame with flattened donor metadata.
        """
        listalldonordf = []

        # HuBMAP entity-api uses donors; SenNet entity-api uses sources.
        # Get only those donors/human sources with metadata.

        if self.consortium == 'hubmapconsortium.org':
            idfield = 'hubmap_id'

            data = {
                "size": 1000,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "entity_type": "donor"
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "term": {
                                    "metadata": ""
                                }
                            }
                        ]
                    }
                },
                "_source": ["hubmap_id", "metadata"]
            }

        else:
            idfield = 'sennet_id'

            data = data = {
                "size": 1000,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "entity_type": "Source"
                                }
                            },
                            {
                                "match_phrase": {
                                    "source_type": "Human"
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "term": {
                                    "source.metadata": ""
                                }
                            }
                        ]
                    }
                },
                "_source": ["sennet_id", "metadata"]
            }

        url = f'{self.urlbase}/search'
        response = requests.post(url=url, headers=self.headers, json=data)

        if response.status_code == 200:

            respjson = response.json()
            # Navigate through the ElasticSearch response.

            donors = respjson.get('hits').get('hits')
            if len(donors) > 0:
                for donor in donors:
                    source = donor.get('_source')
                    donorid = source.get(idfield)
                    dictmetadata = source.get('metadata')
                    if dictmetadata is not None and dictmetadata != {}:
                        # Normalize living_donor_data and organ_donor_data objects.
                        metadata = getmetadatabytype(dictmetadata=dictmetadata)
                        # Flatten metadata to level of donor.
                        donorexport = MetadataFrame(metadata=metadata, donorid=donorid)
                        # Add to list.
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

    def getalldonordoimetadata(self, start: int, end: int, geturls: bool=False) -> pd.DataFrame:
        """
        April 2025
        Extracts from the dfalldonormetadata DataFrame metadata relevant to
        DOIs for published datasets.
        :param start: ordinal number of first donor in a batch to process.
        :param end: ordinal number of the last donor in a batch to process.
        :param geturls: if true, obtain DOI urls for published datasets.
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
            # Get relevant metadata values in lowercase.
            age = donor.loc[donor['grouping_concept'] == 'C0001779']['data_value'].values[0]
            ageunits = donor.loc[donor['grouping_concept'] == 'C0001779']['units'].values[0]
            sex = donor.loc[donor['grouping_concept'] == 'C1522384']['data_value'].values[0].lower()
            race = donor.loc[donor['grouping_concept'] == 'C0034510']['data_value'].values
            if len(race) == 1:
                race = race[0].lower()
            if geturls:
                # Get DOI titles for any published datasets associated with the donor.
                listdatasets = self.getdatasetdoisfordonor(donorid=donorid)
                if len(listdatasets) == 0:
                    listdonor.append({"id": donorid, "age": age, "ageunits": ageunits,
                                      "sex": sex, "race": race,
                                      "doi_url": "no published datasets",
                                      "doi_title": "no published datasets"})
                else:
                    for ds in listdatasets:
                        listdonor.append({"id": donorid, "age": age, "ageunits": ageunits,
                                          "sex": sex, "race": race,
                                          "doi_url": ds.get('doi_url'),
                                          "doi_title": ds.get('doi_title')})

                time.sleep(10)
            else:
                listdonor.append({"id": donorid, "age": age, "ageunits": ageunits,
                                  "sex": sex, "race": race})

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
        hits = dictdonor.get('hits').get('hits')
        descendants = None
        if len(hits) > 0:
            source = hits[0].get('_source')
            if source is not None:
                descendants = source.get('descendants')

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
                        hits = donordataset.get('hits').get('hits')
                        if len(hits) > 0:
                            doi_url = donordataset.get('hits').get('hits')[0].get('_source').get('doi_url')
                            if doi_url is not None:
                                # Get current DOI title from DataCite.
                                doi_title = self.datacite.getdatacitetitle(doi_url=doi_url)
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
        id_field = 'sources.sennet_id'
        source = ["uuid", "doi_url", "registered_doi"]
        dictdonor = self._searchmatch(id_field=id_field, id_value=donorid, source=source)

        descendants = dictdonor.get('hits').get('hits')

        for desc in descendants:
            # Look for DOIs for published datasets.
            source = desc.get("_source")
            doi_url = source.get("doi_url")
            if doi_url is not None:
                # Get current DOI title from DataCite.
                doi_title = self.datacite.getdatacitetitle(doi_url=doi_url)
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
        return getresponsejson(url=url, method='POST', headers=self.headers, json=data)


    def getdoisforconsortium(self, size: int) -> dict:
        """
        Obtain information for the DOIs of published datasets in a consortium.
        :param size: query return size.
        HuBMAP has < 5K published datasets as of April 2025, so use this instead of
        a point in time pagination.

        """

        # The SenNet schema differs from the HuBMAP schema in that SenNet has non-human
        # sources, not just donors.

        if self.consortium == 'hubmapconsortium.org':

            data = {
                "size": size,
                "sort": [
                    {
                        "registered_doi.keyword": {
                            "order":"asc"
                        }
                    }
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "entity_type": "dataset"
                                }
                            },
                            {
                                "match_phrase": {
                                    "status": "Published"
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "term": {
                                    "registered_doi": ""
                                },
                                "term": {
                                    "donor.metadata": ""
                                }
                            }
                        ]
                    }
                },
                "_source": ["donor.hubmap_id", "registered_doi"]
            }

        else:

            data = {
                "size": size,
                "sort": [
                    {
                        "registered_doi.keyword": {
                            "order": "asc"
                        }
                    }
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "entity_type": "dataset"
                                }
                            },
                            {
                                "match_phrase": {
                                    "status": "Published"
                                }
                            },
                            {
                                "match_phrase": {
                                    "sources.source_type": "Human"
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "term": {
                                    "registered_doi": ""
                                },
                                "term": {
                                    "donor.metadata": ""
                                }
                            }
                        ]
                    }
                },
                "_source": ["sources.sennet_id", "registered_doi"]
            }

        url = f'{self.urlbase}/search'
        return getresponsejson(url=url, method='POST', headers=self.headers, json=data)

    def getdonorraceandageterms(self, donorid: str) -> dict:
        """
        Returns a dict of case-insensitive terms for a donor's race and age
        :param donorid: hubmap or sennet id
        :return:
        """

        if self.consortium == 'hubmapconsortium.org':
            id_field = 'hubmap_id'
        else:
            id_field = 'sennet_id'

        # Search for donor
        donor = self._searchmatch(id_field=id_field, id_value=donorid, source =["metadata"])

        if donor is None:
            print(f'Error: missing donor {donorid}')
            exit(-1)
        else:
            metadata = donor.get('hits').get('hits')[0].get('_source').get('metadata')
            if 'living_donor_data' in metadata.keys():
                listkey = 'living_donor_data'
            else:
                listkey = 'organ_donor_data'
            listmeta = metadata.get(listkey)
            # Get terms for race and sex.
            for m in listmeta:
                grouping_concept = m.get('grouping_concept')
                if grouping_concept == 'C1522384':
                    # sex
                    sex = m.get('preferred_term').lower()
                elif grouping_concept == 'C0034510':
                    # race
                    race = m.get('preferred_term').lower()

            dictret = {'race': race, 'sex': sex}
            return dictret


