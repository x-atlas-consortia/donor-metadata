"""
Class representing interactions with the DataCite API for DOIs.
"""
import os
import sys
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
                "doi": id.upper(),
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

        print(f'Getting remaining {str(pages-1)} pages...')
        for page in tqdm(range(2,pages+1)):
            url_next = f'{url_init}&page[number]={page}'
            response_next = getresponsejson(url=url_next, method='GET')

            if response_next is not None:
                data_next = response_next.get('data')
                listret = listret + self._gettitleinfo(data=data_next)

        return listret

    def getdoititles(self) -> pd.DataFrame:
        """

        Returns DataFrame with titles of all published DOIs for a consortium.
        Includes parsed race and sex terms.

        """

        listret = []
        print('Obtaining all DOI titles for consortium...')
        listtitles = self.getalldatacitetitles()
        if listtitles is None:
            print('Error from DataCite')
            exit(-1)

        for doi in listtitles:
            title = doi.get('title')
            if title is not None:
                dictparse = self._parsedtitle(title=title)
            listret.append(
                {
                    "doi": doi.get('doi'),
                    "title": title,
                    "race": dictparse.get('race'),
                    "sex": dictparse.get('sex'),
                    "age": dictparse.get('age'),
                    "ageunits": dictparse.get('ageunits')
                }
            )

        return pd.DataFrame(listret).drop_duplicates()

    def _parsedtitle(self, title: str) -> dict:
        """
        Parses the age, age unit, sex, and race terms from a DOI title string.
        :param title: DOI title string
        :return: dict
        """

        # The DOI title is expected to be in format
        # <type of data> from the <organ> of a <age>-<age unit>-old <race> <sex>.
        # The race can have multiple words--e.g., "black or african american".

        dictret = {}
        title = title.lower().replace(' donor', '')
        if '-old' in title:
            # Extract the combined race and sex phrase.
            doiracesex = title.split('-old ')[1]
            # format of doiracesex:
            #   <race> <sex>
            # The term for sex is the last word in the combined phrase.
            racesexsplit = doiracesex.split(' ')
            doisex = racesexsplit[len(racesexsplit) - 1]
            # The term for race is everything up to the sex term.
            doirace = doiracesex[0:(doiracesex.find(doisex) - 1)]
            dictret['race'] = doirace
            dictret['sex'] = doisex

            # Extract the age unit.
            doiage = title.split('-old')[0]
            # format of doiage:
            #   <type of data> from the <organ> of a <age>-<age unit>
            dashsplit = doiage.split('-')
            if len(dashsplit) > 1:
                # format of doiagedashsplit:
                #   <type of data> from the <organ> of a <age>
                #   <age unit>
                dictret['ageunits'] = dashsplit[len(dashsplit)-1]
            else:
                dictret['ageunits'] = 'age unit cannot be parsed'

            # Extract the age.
            doiage = title.split('of a')
            # format of doiage:
            #   <type of data> from the <organ>
            #   <age>-<age unit>-old <race> <sex>
            dashsplit = doiage[1].split('-')
            if len(dashsplit) > 1:
                dictret['age'] = dashsplit[0].strip()
            else:
                dictret['age'] = 'age cannot be parsed'

        else:
            dictret['race'] = 'race cannot be parsed'
            dictret['sex'] = 'sex cannot be parsed'
            dictret['age'] = 'age cannot be parsed'
            dictret['ageunits'] = 'ageunits cannot be parsed'

        return dictret