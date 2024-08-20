# HuBMAP/SenNet Donor Clinical Metadata data entry application

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

All types of metadata are associated with discrete codes. Codes that describe a particular type of data
are collected into valuesets and maintained in spreadsheets.

Because we have few expectations regarding the form of 
clinical data from providers, it is usually necessary to update the valueset 
spreadsheet with every set of donors. 

# Solution
The ideal curation solution has features including:
- A form that allows
   - data entry--e.g., selection of categorical values or entry of numeric or text values
   - validation--e.g., data type and range
   - unlimited values--e.g., many entries for patient medical history
- Encoding of each metadata element to appropriate valuesets
- Ability to update a neo4j provenance database by:
  - connecting to the database
  - preparing and executing a Cypher insert query

# Architecture
## Elements
- Python
- Flask/WTF for forms-based app
- neo4j driver
- Docker 

_Diagram pending_ 