# HuBMAP/SenNet Human Donor Clinical Metadata Curator application

# Background
## Donor clinical metadata
When registering datasets generated from tissues that came 
from human donors, providers such as HuBMAP Tissue Mapping Centers (TMCs) include
clinical information about donors. Clinical information varies in detail and
scope: a common source of clinical information for a tissue sample are the UNOS forms that 
accompany an organ donation.

In general, clinical information is both unstructured and considered Patient Health Information (PHI) per 
HIPAA. The University of Pittsburgh, acting as a HIPAA Honest Broker, curates
the clinical information, creating data that are:
1. De-identified
2. Encoded, or associated with codes from standard biomedical vocabularies, including SNOMEDCT.

Up to now, curation has been manual: the curator manually encodes information from source files into
a data entry spreadsheet, following [this process](https://docs.google.com/document/d/1ILlkcaD0wo3CGz7ceh5ikjHQA-2owOfmQRR9CgAkcl4/edit#heading=h.p81z9ilnkp3o). The spreadsheet becomes the input source for a script that inserts
donor clinical metadata into the associated dataset record in the provenance database.

Manual curation is both tedious and prone to error. Curation can be automated.

## Valuesets
Clinical metadata of interest is one of three types:
1. Numeric
2. Categorical
3. Free text

Each type of metadata is associated with discrete codes. 
Codes that describe a particular type of data are collected into valuesets and 
maintained in spreadsheets. 
Categorical metadata may be stored in one of two ways:
1. in a dedicated tab in the spreadsheet (e.g., Race)
2. as a set of rows in a tab (e.g., ABO blood types in the Blood Type tab)

We have few expectations regarding the form of 
clinical data from providers beyond the minimum set required to build a DOI for a dataset (race; sex; age; whether 
organ or living). Clinical data from a provider often contains novel information--e.g., 
previously undocumented medical history conditions or measurements.

In general, it is necessary to update the valueset spreadsheet for every set of donors. 

# Solution
The curation solution features:
- A user interface that allows
   - data entry--e.g., selection of categorical values or entry of numeric or text values
   - validation--e.g., data type and range
   - multiple entries for patient medical history
- Encoding of each metadata element to appropriate valuesets
- Form content driven by the valueset spreadsheet to allow rapid changes in valuesets
- Ability to update a neo4j provenance database for a donor

# Architecture
## Application
The curator is a Python Web application involving:
  - Python
  - Flask
  - Flask Blueprints
  - WTForms
  - Jinja2
  - neo4j driver
  - HTML
  - JavaScript
## Configuration
The app.cfg for the application is used to set:
- consortium (HuBMAP or SenNet)
- entity-api environment
- the consortium-specific authorization token
## Databases
The application works with three databases:
1. The Google Sheets document of valueset information.
2. The neo4j provenance databases for the two consortia, as abstracted by consortium-specific instances of entity-api.
## Docker
_to do_ 

# Development
## Initial tasks
* Install all packages in *requirements.txt*.