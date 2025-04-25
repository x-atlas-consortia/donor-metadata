# Validation scripts
April 2025 

## Scope
This folder contains scripts that were developed to address 
issues related to formatting of donor metadata, including:

1. changes in donor race and sex that require updates to titles for DOIs of published datasets
2. accomodating variable formats for numeric data (integer and decimal)

The **donor-metadata** Flask application is intended primarily as a means to edit the metadata of 
one donor at a time, and is not suitable for bulk validation.

The validation scripts use classes that were originally developed for the
**donor-metadata** application, including:
- searchapi.py
- datacite.py

The classes have been enhanced to allow use by either the Flask app or the validation scripts.

## doi_donor.py
### Prerequisites
Unlike the **donor-metadata** application, this script does not use Globus SSO.
A file named **globus.token** must contain an appropriate, current Globus groups token.
The file is ignored by **.gitignore**.

### Parameter
The **-c** (**--consortium) identifies the environment:
- h: HuBMAP
- s: SenNet

### Actions
The **doi_donor.py** script:
1. Uses the consortium-appropriate **search-api** to obtain information on:
   - donors (human sources in SenNet) with metadata
   - published datasets with DOIs
2. Parses clinical metadata for donors relevant to DOI titles:
   - age
   - age units
   - sex
   - race
3. Calls the DataCite API to obtain titles for all DOIs of a consortium.
4. Parses from DOI titles clinical metadata for associated donors. 
5. Compares clinical metadata of donors with clinical metadata in the titles of DOIs associated with donors.
6. Writes results to output.

## DOI title format
The standard format for a DOI title is:

*type of data* from the *organ* of a *age*-*age unit*-old *race* *sex*

Example:
`multiplex ion beam imaging data from the uterus of a 25.1-year-old black or african american female`

The script can only parse metadata from titles in the expected format.

### Output files
Output files are ignored by **.gitignore**.

### *consortium*_doi_donor_analysis.csv
Each row corresponds to a DOI.
Columns

#### donorid
The HubMAP or SenNet id of the donor
#### doi
The DOI of the published dataset
#### age_donor, ageunits_donor, race_donor, sex_donor
Clinical metadata for the donor
#### title
DOI title from DataCite Commons
#### age_doi, ageunits_doi, race_doi, sex_doi
Clinical metadata parsed from the DOI title
#### age_match, ageunits_match, race_match, sex_match
Whether the clinical metadata field for the donor matches the corresponding field from the DOI
#### match
Whether all clinical metadata fields match
#### age_donor_type, age_doi_type
Numeric type of an age field. This is to identify the particular case in which a donor's age is of a different numeric type 
than the age in the DOI title--e.g., if the donor's age is 44 years, but
the DOI reads "44.0". 

When Excel opens a CSV file, it casts string values that represent whole number decimals to integer. 
This can obscure issues of the age numeric type.

### *consortium*_donors_to_update.csv
A unique list of identifiers for donors with published datasets
with DOIs that need to be updated.