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


def checkageunit(row) -> str:
    """
    Compares the singular age unit from the DOI (e.g., year) with the
    plural age unit from donor metadata (e.g., years).

    :return: yes or no
    """
    doiunitplural = f'{row["ageunits_doi"]}s'
    if doiunitplural == row["ageunits_donor"]:
        return 'yes'
    else:
        return 'no'

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
dfdonordoi = getdoianddonorid(consortium=consortium, search=search)

# Obtain all DOI-related donor metadata for the consortium.
print('Getting donor metadata for consortium...')
search.dfalldonormetadata = search.getalldonormetadata()

# Find any data_value with trailing zeroes.
dftz = search.dfalldonormetadata
dftz['last_digit'] = [str(x).strip()[-1] for x in dftz['data_value']]
dftz['decimal'] = ['.' in str(x) for x in dftz['data_value']]
dftz['trailing_zero'] = np.where((dftz['last_digit'] =='0') & (dftz['decimal']), 'yes', 'no')
dftz = dftz[['id', 'trailing_zero']]

dfdonordoitz = pd.merge(left=dfdonordoi, right=dftz,
                        how='left', left_on='donorid', right_on='id')
dfdonordoitz = dfdonordoitz.drop('id', axis=1)

print('Filtering to DOI-specific metadata...')
start = 0
end = len(search.dfalldonormetadata)
dfdonor = search.getalldonordoimetadata(start=start, end=end, geturls=False)


# Obtain all consortium DOIs from DataCite.
dfdoi = datacite.getdoititles()

print('Comparing donor metadata with DOI metadata...')
# Merge doi-donor map with donor metadata.
dfdoidonor = pd.merge(left=dfdonordoitz, right=dfdonor,
                 how='left', left_on='donorid', right_on='id')

# Merge doi-donor with metadata with parsed doi title information.
dfout = pd.merge(left=dfdoidonor, right=dfdoi,
                 how='left', on='doi',
                 suffixes=['_donor','_doi'])

# Compare terms for race and sex from donor metadata with corresponding
# terms parsed from the DOI titles.
dfout['race_match'] = np.where(dfout['race_doi'] == dfout['race_donor'],
                               'yes', 'no')
dfout['sex_match'] = np.where(dfout['sex_doi'] == dfout['sex_donor'],
                              'yes', 'no')
dfout['age_match'] = np.where(dfout['age_doi'] == dfout['age_donor'],
                              'yes', 'no')
# Age unit is singular in DOI title and plural in donor metadata.
dfout['ageunits_match'] = dfout.apply(checkageunit, axis=1)

dfout['match'] = np.where(
    (dfout['race_match'] == 'yes')
    & (dfout['sex_match'] == 'yes')
    & (dfout['age_match'] == 'yes')
    & (dfout['ageunits_match'] == 'yes'),
    'yes', 'no')

# Explicitly compare number types of donor and doi age to identify synchronization
# issues--e.g., an integer donor age (11) and a decimal DOI age (11.0).
# (When Excel opens a CSV with a decimal in format x.0, it truncates the display, so
# the numeric type mismatch is not apparent.)
dfout['age_donor_type'] = np.where(dfout['age_donor'].str.contains('.', regex=False), 'decimal', 'integer')
dfout['age_doi_type'] = np.where(dfout['age_doi'].str.contains('.', regex=False), 'decimal', 'integer')
# Drop extra id column.
dfout = dfout.drop('id', axis=1).sort_values(by='donorid')

# Write to output.
print('Writing output files...')
cout = consortium.split('_')[1]
outfile = f'{cout}_doi_donor_analysis.csv'
dfout.to_csv(outfile, index=False)

# Export only donorids with datasets that need DOI updates.
dfid = dfout[dfout['match'] == 'no']['donorid'].drop_duplicates()
idfile = f'{cout}_donors_to_update.csv'
dfid.to_csv(idfile, index=False)

# Export only donorids with metadata with trailing zeroes.
dfzero = dfout[dfout['trailing_zero'] == 'yes']['donorid'].drop_duplicates()
idfile = f'{cout}_donors_trailing_zeroes.csv'
dfzero.to_csv(idfile, index=False)


