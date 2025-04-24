"""
April 2025

Script to compare the following:
1. Titles of DOIs for published datasets
2. Donor clinical metadata

e.g., for a DOI with a title of "...from a 65-year-old white male...." ,
the script compares whether the race of the donor is "white" and the sex "male".

This was intended to support a one-time correction of donor metadata, but uses
classes of the donor-metadata flask app.
"""
import pandas as pd
import numpy as np

from callapi import readglobustoken, getconsortiumfromargs

import os
import sys
from tqdm import tqdm
# import time
import csv

# Import SearchAPI class originally developed for the donor-metadata app.

# The following allows for an absolute import from an adjacent script directory--i.e., up and over instead of down.
# Find the absolute path.
fpath = os.path.dirname(os.getcwd())
fpath = os.path.join(fpath, 'app/models')
sys.path.append(fpath)
from searchapi import SearchAPI


def getdoianddonorid(consortium: str, search: SearchAPI) -> pd.DataFrame:

    """
    Returns DataFrame of dataset information for validation.
    :param consortium: name of consortium
    :param search: SearchAPI instance
    :return: a list of dictionaries with;
             registered DOI
             donor id
    """
    listret = []

    print('Getting information on published datasets...')

    # Get all DOIs for published datasets.
    datasets = search.getdoisforconsortium(size=5000)
    if 'error' in datasets.keys():
        print(datasets)
        exit(-1)

    # Flatten response.
    if datasets is not None:
        hits = datasets.get('hits').get('hits')
        for hit in hits:
            source = hit.get('_source')
            registered_doi = source.get('registered_doi')
            if consortium == 'CONTEXT_HUBMAP':
                donorid = source.get('donor').get('hubmap_id')
            else:
                donorid = source.get('sources')[0].get('sennet_id')

            listret.append({'donorid': donorid, 'doi': registered_doi})

        # Convert to DataFrame, dropping cases of published datasets without DOIs.
        return pd.DataFrame(listret).dropna(subset=['doi'])

def getdoititles(consortium: str, search: SearchAPI) -> pd.DataFrame:
    """

    Returns DataFrame with titles of all published DOIs for a consortium.
    Includes parsed race and sex terms.
    :param consortium: name of consortium
    :param search: SearchAPI instance
    """

    listret = []
    print('Obtaining all DOI titles for consortium...')
    listtitles = search.getalldatacitetitles()
    if listtitles is None:
        print('Error from DataCite')
        exit(-1)

    for doi in listtitles:
        title = doi.get('title')
        if title is not None:
            dictparse = parsedtitle(title=title)
        listret.append(
            {
                "doi": doi.get('doi'),
                "title": title,
                "race": dictparse.get('race'),
                "sex": dictparse.get('sex')
            }
        )

    return pd.DataFrame(listret).drop_duplicates()

def parsedtitle(title: str) -> dict:
    """
    Parses the sex and race terms from a DOI title string.
    :param title: DOI title string
    :return: dict
    """

    # The DOI title is in format
    # <type of data> from the <organ> of a <age>-<age unit>-old <race> <sex>.
    # The race can have multiple words--e.g., "black or african american".

    dictret = {}
    title = title.lower().replace(' donor','')
    if 'old' in title:
        # Extract the combined race and sex phrase.
        doiracesex = title.split('old ')[1]
        # The term for sex is the last word in the combined phrase.
        racesexsplit = doiracesex.split(' ')
        doisex = racesexsplit[len(racesexsplit)-1]
        # The term for race is everything up to the sex term.
        doirace = doiracesex[0:(doiracesex.find(doisex)-1)]

        dictret['race'] = doirace
        dictret['sex'] = doisex

    else:
        dictret['race'] = 'race cannot be parsed'
        dictret['sex'] = 'sex cannot be parsed'

    return dictret


def writetocsv(filename: str, line: dict):
    """
    Writes to a csv file.
    :param filename: name of output file.
    :param line: dict of information to write. If empty,creates a new file with a header.
    :return: none
    """
    if line == {}:
        fmt = 'w'
        lineout = ['doi', 'title', 'race', 'sex',
                   'donorid']
    else:
        fmt = 'a'
        lineout = [
            line['doi'],
            line['title'],
            line['race'],
            line['sex'],
            line['donorid']
        ]

    with open(filename, fmt, newline='') as csvfile:

        cw = csv.writer(csvfile, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
        cw.writerow(lineout)


# --- MAIN
# Get the consortium.
consortium = getconsortiumfromargs()
# Get the Globus token from file.
token = readglobustoken()

# Set up the search-api interface.
search = SearchAPI(consortium=consortium, token=token)

# Obtain information on published datasets.
dfdoi = getdoianddonorid(consortium=consortium, search=search)

# Obtain all HuBMAP DOIs from DataCite.
dftitles = getdoititles(consortium=consortium, search=search)
print(dftitles)
exit(-1)

# List of unique donor metadata.
listdonor = []

# Start output file.
outfile= 'doi_data.csv'
writetocsv(filename=outfile, line={})

# Get DOI titles from DataCite.


