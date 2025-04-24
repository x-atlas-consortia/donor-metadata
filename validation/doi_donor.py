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
# to obtain DOI information for published datasets
from datacite import DataCiteAPI


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
# Set up the DataCite API interface.
datacite = DataCiteAPI(consortium=consortium)

# Obtain information on published datasets and their donors.
dfdoidonor = getdoianddonorid(consortium=consortium, search=search)

# Obtain all DOI-related donor metadata for the consortium.
print('Getting donor metadata for consortium...')
search.dfalldonormetadata = search.getalldonormetadata()
start = 0
end = len(search.dfalldonormetadata)
dfdonor = search.getalldonordoimetadata(start=start, end=end, geturls=False)
dfout = dfdonor
# Obtain all consortium DOIs from DataCite.
#dfdoi = datacite.getdoititles()

# Merge doi-donor map with donor metadata.
#dfout = pd.merge(left=dfdoidonor, right=dfdonor,
                 #how='left', left_on='donorid', right_on='id')

# Start output file.
outfile= 'doi_donor.csv'
dfout.to_csv(outfile, index=False)



