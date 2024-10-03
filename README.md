# HuBMAP/SenNet Human Donor Clinical Metadata Curator application

# Background
## Donor clinical metadata
When registering datasets generated from tissue samples collected from human donors, providers such as HuBMAP Tissue Mapping Centers (TMCs) include
clinical information about donors. Clinical information on a donor varies in detail and
scope, ranging from a spreadsheet row with a few curated elements to scans of UNOS forms that 
accompany an organ donation.

In general, clinical information is both unstructured and considered Patient Health Information (PHI) per 
HIPAA. The University of Pittsburgh, acting as a HIPAA Honest Broker, curates
clinical information, creating metadata data that are:
1. de-identified
2. _encoded_, or associated with codes from standard biomedical vocabularies such as SNOMEDCT and NCI.

Up to now, curation has been manual: the curator manually encodes information from source files into
a data entry spreadsheet, following [this process](https://docs.google.com/document/d/1ILlkcaD0wo3CGz7ceh5ikjHQA-2owOfmQRR9CgAkcl4/edit#heading=h.p81z9ilnkp3o). The spreadsheet becomes the input source for a script that inserts
donor clinical metadata into the associated dataset record in the provenance database.

Manual curation is both tedious and prone to error. Curation can be automated.

## Valuesets
Clinical metadata of interest is one of three types:
1. Numeric (e.g., lab values, measurements such as height)
2. Categorical (e.g., Cause of Death, blood type)
3. Free text

Each type of metadata can be associated with discrete codes. 
Codes that describe a particular type of data are collected into valuesets and 
maintained in an online _Valuset Manager_ spreadsheet. 

Categorical metadata may be organized in the Valueset Manager in one of two ways:
1. in a dedicated tab in the spreadsheet (e.g., Race)
2. as a set of rows in a tab (e.g., ABO blood types in the Blood Type tab)

We have few expectations regarding the form of 
clinical data from providers beyond the minimum set required to build a DOI for a dataset:
* race
* sex
* age
* whether from an organ donor or a living donor 

Clinical data from a provider often contains novel information--e.g., 
previously undocumented medical history conditions or measurements. 

In general, it is necessary to update the Valueset Manager spreadsheet for every set of donors. 

# Solution
The curation solution features:
- A user interface that allows
   - data entry--e.g., selection of categorical values or entry of numeric or text values
   - validation--e.g., data type and range
   - multiple entries for patient medical history
- Encoding of each metadata element to appropriate valuesets
- Form content driven by the valueset spreadsheet to allow rapid changes in valuesets
- Ability to update a neo4j provenance database with structured clinical metadata for a donor

# Solution Architecture
## User Interface
The curator is a Python Web application involving:

| tool                                                                            | purpose                                                      |
|---------------------------------------------------------------------------------|--------------------------------------------------------------|
| Python                                                                          | application function                                         |
| [Flask](https://flask.palletsprojects.com/en/3.0.x/)                            | Python web framework                                         |
| [Flask Blueprints](https://flask.palletsprojects.com/en/3.0.x/blueprints/)      | modular Flask applications                                   |
| [WTForms](https://wtforms.readthedocs.io/en/2.3.x/forms/)                       | forms in Flask applications                                  |
| [Jinja](https://jinja.palletsprojects.com/en/3.1.x/)                            | Web page templating                                          |
| Javascript                                                                      | Event handling and UI features (including a spinner control) |
| [Bootstrap](https://getbootstrap.com/)                                          | UI toolkit                                                   |
| [HuBMAP entity-api](https://smart-api.info/ui/0065e419668f3336a40d1f5ab89c6ba3) | Reads/updates donor metadata in HuBMAP provenance            |
| [SenNet entity-api](https://smart-api.info/ui/7d838c9dee0caa2f8fe57173282c5812) | Reads/updates human source metadata in SenNet provenance     |


## Configuration
The application uses **app.cfg** to obtain:
- consortium options (HuBMAP or SenNet)
- entity-api environment (e.g., development or production)

## Databases
The application works with three databases:
1. the Valueset Manager, a Google Sheets document
2. the neo4j provenance databases for the two consortia, abstracted by consortium-specific instances of entity-api.

## Workflow
![Curator application architecture.jpg](doc%2FCurator%20application%20architecture.jpg)

### app
The application:
1. uses the **valuesetmanager** helper class to read from the Valueset Manager spreadsheet
2. manages the Flask session
3. registers Flask Blueprints
4. customizes HTTP error handling, routing to **401.html**

### Home (search) page
1. The Home HTML page **index.html** includes a form that allows the user to specify 
   * consortium (HuBMAP or SenNet)
   * Donor ID
   * consortium-specific authentication token
2. The WTForm **searchform.py** populates **index.html** with information from the **app.cfg** file.
3. The Blueprint route **seach.py**:
   * sets/reads an authentication token from a session cookie
   * works with the **donor** helper class to verify that the donor is in provenance
   * redirects either to the Edit page or the custom 401 page

### Edit page
1. The Edit page **edit.html** includes a form that allows metadata data entry.
2. The WTForm **editform.py**:
   * works with the **valuesetmanager** helper class to obtain valueset content
   * populates the form in **edit.html**, including content of categorical lists
3. The Blueprint route **edit.py**:
   * works with the **donor** helper class to obtain current donor metadata from provenance
   * populates the form in **edit.html** with current metadata values
   * translates form data into a revised metadata JSON that conforms to the donor metadata schema in provenance.
   * sets defaults for required metadata--e.g., if no race is specified, sets the race to Unknown
   * converts linear and weight measurements to metric units
   * compares current and revised metadata JSON for the donor
   * posts JSONs for current metadata, revised metadata, and comparison to **review.html**

### Review page
1. The Review page **review.html** displays:
   * the current metadata JSON for the donor
   * the new metadata JSON for the donor
   * the comparison of the current and new metadata JSONs
2. The Blueprint route **review.py**:
   * works with the **donor** helper class to update the donor metadata in provenance
   * redirects to **index.html**

### Token page
The Token page **token.html** is a static page with instructions on how to obtain an authentication cookie for a particular consortium.

### 401 page
The **401.html** page is a custom 401 error that explains potential causes and solutions for authentication errors.

### base.html
All HTML files in the application inherit from **base.html**, which includes:
* a navbar
* a message panel that displays Flask flash messages
* a spinner control to animate waiting in the search form

### _formhelpers.html
This file contains a custom Jinja script used to populate content from WTForms forms in a HTML page.

### Helper classes

| name            | role                                           | uses       |
|-----------------|------------------------------------------------|------------|
| appconfig       | reads from the app.cfg                         |            |
| valuesetmanager | reads from the Valueset Manager spreadsheet    |            |
| entity          | reads from and writes to a provenance database | entity-api |
| donor           | represents donor metadata                      | entity     |
| DonorUI         | encapsulates the Flask app                     | app        |


## Business rules
1. The application will not update metadata for a donor that is associated with published datasets. 
2. The application can document a maximum of 10 medical conditions. The application cannot update metadata for a donor if the current metadata includes more than 10 conditions.
3. The application will not update metadata if there was no change.

## Authentication token
The entity-api requires an authentication token. An authentication token for a consortium's entity-api are set via the consortium's Single Sign On. 
The **token.html** page provides instructions on how to obtain the authentication token.
The user enters an authentication token in the form in the home page.

The application caches the authentication token in a session cookie. 
Caching the token facilitates the curation of multiple donors in a session: it is not necessary to supply the token for each donor.

Although the token has a long expiration period (72 hours), the application expires the session cookie after 5 minutes. It is also possible to clear the session cookie in the home page.

## Docker
_to do_ 
