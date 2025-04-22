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

from callapi import readglobustoken, getconsortiumfromargs

import os
import sys
from tqdm import tqdm
import pandas as pd

# Import SearchAPI class originally developed for the donor-metadata app.

# The following allows for an absolute import from an adjacent script directory--i.e., up and over instead of down.
# Find the absolute path.
fpath = os.path.dirname(os.getcwd())
fpath = os.path.join(fpath, 'app/models')
sys.path.append(fpath)
from searchapi import SearchAPI

def getdoianddonorid(consortium: str) -> list:

    """
    Returns flattened dict of dataset information for validation.
    :param consortium: name of consortium
    :return: a list of dictionaries with;
             registered DOI
             donor id
    """
    listret = []

    print('Getting information on published datasets...')

    # Get all DOIs for published datasets.
    datasets = search.getdoisforconsortium(size=10)
    if datasets is not None:
        hits = datasets.get('hits').get('hits')

        for hit in hits:
            source = hit.get('_source')
            registered_doi = source.get('registered_doi')
            if consortium == 'CONTEXT_HUBMAP':
                idfield = 'hubmap_id'
            else:
                idfield = 'sennet_id'
            donorid = source.get('donor').get(idfield)

            listret.append({'donorid': donorid, 'doi':'registered_doi'})

        return listret


# --- main
# Get the consortium.
consortium = getconsortiumfromargs()
# Get the Globus token from file.
token = readglobustoken()

# Set up the search-api interface.
search = SearchAPI(consortium=consortium, token=token)

# Obtain information on published datasets.
listdsinfo = getdoianddonorid(consortium=consortium)

# For each published dataset,

# 2. Get the terms for donor's metadata for sex and race.
# 3. Get the DOI title from DataCite.
# 4. Write to a spreadsheet.
