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
    datasets = search.getdoisforconsortium(size=3)
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

        return listret


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
    # Extrct the combined race and sex phrase.
    print(title)
    doiracesex = title.split('old ')[1]
    # The term for sex is the last word in the combined phrase.
    racesexsplit = doiracesex.split(' ')
    doisex = racesexsplit[len(racesexsplit)-1]
    # The term for race is everything up to the sex term.
    doirace = doiracesex[0:(doiracesex.find(doisex)-1)]

    dictret['race'] = doirace
    dictret['sex'] = doisex

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
listdsinfo = getdoianddonorid(consortium=consortium)

# List of unique donor metadata.
listdonor = []

# Start output file.
outfile= 'doi_data.csv'
writetocsv(filename=outfile, line={})

# For each published dataset,
# 1. Get the DOI title from DataCite.
# 2. Extract the race and sex terms from the title.
# 3. Get the donor id.
# 4. Write to output.

print('Parsing DOI title terms for race and sex...')
for ds in tqdm(listdsinfo):

    doi = ds.get("doi")
    doi_url = f'https://doi.org/{doi}'
    title = search._getdatacitetitle(doi_url=doi_url)
    ds['title'] = title

    dictparsedtitle = parsedtitle(title=title)
    ds['race'] = dictparsedtitle.get('race')
    ds['sex'] = dictparsedtitle.get('sex')

    # Get donor id
    listdonor.append(ds.get('donorid'))

    # Write to CSV as we go to minimize memory.
    writetocsv(filename=outfile, line=ds)

# Make list of donors unique.
listdonor = list(set(listdonor))

print('Parsing terms for sex and race from associated donors...')
listdonormeta = []

for donorid in listdonor:
    metadata = search.getdonorraceandageterms(donorid=donorid)
    donormeta ={'donorid': donorid,
                'race': metadata['race'],
                'sex': metadata['sex']}
    listdonormeta.append(donormeta)

# Merge and compare DOI and unique donor metadata via Pandas.

# Get doi metadata from CSV.
dfdoi = pd.read_csv(outfile)
# Convert unique donor metadata to DataFrame.
dfdonor = pd.DataFrame(listdonormeta)
# Merge on the donorid.
dfout = pd.merge(left=dfdoi, right=dfdonor, how='left', on='donorid',
                 suffixes=['_doi','_donor']).sort_values(by='donorid')
# Compare terms.
dfout['race_match'] = np.where(dfout['race_doi'] == dfout['race_donor'],
                               'yes', 'no')
dfout['sex_match'] = np.where(dfout['sex_doi'] == dfout['sex_donor'],
                              'yes', 'no')
# Write to CSV.
dfout.to_csv(outfile, index=False)

