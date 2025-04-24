"""
Class representing interactions with the DataCite API for DOIs.
"""
import os
import sys

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

class DataCiteAPI:

    def __init__(self, consortium: str):
        """
        :param consortium: name of the globus consortium (HuBMAP, SenNet)

        """

        # Base for all DOI requests to DataCite.
        self.urlbase = 'https://api.datacite.org/dois/'

        # Specific DataCite clients
        if consortium.upper() == 'CONTEXT_HUBMAP':
            self.clientid = 'psc.hubmap'
        else:
            self.clientid = 'psc.sennet'

    def getdatacitetitle(self, doi_url: str) -> str:
        """
        Queries the DataCite REST API for the title of a DOI.
        """

        doi = doi_url.split('https://doi.org/')[1]
        url = f'https://api.datacite.org/dois/{doi}'
        response = getresponsejson(url=url, method='GET')
        if response is not None:
            return response.get("data").get("attributes").get("titles")[0].get("title")

    def _gettitleinfo(self, data:list) -> list:
        """
        Parses information from the data list of a DataCite response.
        :param data: data list
        :return: list of dicts of flattened information
        """

        listtitle = []
        for doi in data:
            id = doi.get('id')
            titles = doi.get('attributes').get('titles')
            if len(titles) > 0:
                title = titles[0].get('title')
            listtitle.append({
                "doi": id,
                "title": title
            })
        return listtitle

    def getalldatacitetitles(self) -> list:
        """
        Obtains titles for all DOIs for a consortium.
        Uses pagination.
        :return: list of dicts of flattened information.
        """
        listret = []



        print('Getting initial page of 1000 titles...')
        # Obtain the first 1000 records and pagination parameters.
        url_init = f'https://api.datacite.org/dois/?client-id={self.clientid}&fields[dois]=titles&page[size]=1000'
        response_init = getresponsejson(url=url_init, method='GET')

        if response_init is not None:
            data = response_init.get('data')
            listret = listret + self._gettitleinfo(data=data)

        pages = response_init.get('meta').get('totalPages')

        for page in range(2,pages+1):
            print(f'Getting page {str(page)} of 1000 titles...')
            url_next = f'{url_init}&page[number]={page}'
            response_next = getresponsejson(url=url_next, method='GET')

            if response_next is not None:
                data_next = response_next.get('data')
                listret = listret + self._gettitleinfo(data=data_next)

        return listret