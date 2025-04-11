"""
Form used to build the JSON of new metadata for a donor in provenance.
Second form in the curation workflow.
"""
import os

from wtforms import (Form, StringField, SelectField, DecimalField, validators, ValidationError,
                     TextAreaField, SubmitField)

# Helper classes
# Represents the app.cfg file
from models.appconfig import AppConfig
# Represents the Google Sheets of donor clinical metadata valuesets
from models.valuesetmanager import ValueSetManager
from models.stringnumber import stringisintegerorfloat


def validate_age(form, field):
    """
    Custom validator. Checks that age is at least 1 month.

    :param form: the Edit form
    :param field: the age field
    :return: Nothing or raises ValidationError
    """

    ageunit = form.ageunit.data
    age = field.data
    print(age)
    # if not age.isnumeric():
    if not stringisintegerorfloat(age):
        raise ValidationError('Age must be a number.')
    agenum = float(age)

    # Apr 2025 - Set minimum age to be 1 month.
    if agenum <= 0:
        raise ValidationError('The minimum age is 1 month.')
    # if age is None:
        # age = 0
    if agenum > 89 and ageunit == 'C0001779':  # UMLS CUI for age in years
        if agenum != 90:
            raise ValidationError('All ages over 89 years must be set to 90 years.')


def validate_selectfield_default(form, field):
    """
    Custom validator that checks whether the value specified in a SelectField's data property is in
    the set of available values.
    Handles the case of where there is a mismatch between an existing metadata value for a donor and the
    corresponding SelectField in the Edit form.

    :return: nothing or ValidationError
    """
    found = False
    for c in field.choices:
        if field.data == c[0]:
            found = True
    if not found:
        msg = f"Selected concept '{field.data}` not in valueset."
        raise ValidationError(msg)


def validate_required_selectfield(form, field):
    """
    Custom validator that verifies that the value specified in a SelectField deemed required (e.g., Source)
    is other than the prompt.

    """
    if field.data == 'PROMPT':
        msg = f'Required'
        raise ValidationError(msg)


# ----------------------
# MAIN FORM


class EditForm(Form):

    # POPULATE FORM FIELDS. In particular, populate SelectFields with lists obtained from the valueset manager.

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Instantiate the ValuesetManager that reads resources for form controls from a
    # Google Sheet.
    # Get URL to Google sheet, with single quote literals stripped.
    url = cfg.getfield(key='VALUESETMANAGER')

    # Export path for valueset spreadsheet.
    fpath = cfg.path + '/valuesets.xlsx'
    # Download current version of valueset data.
    valuesetmanager = ValueSetManager(url=url, download_full_path=fpath)

    # Application context for entity-api URLs (HuBMAP or SenNet).
    # This field will be used to build the appropriate endpoint URL.
    # This field will be populated by the edit route, based on information passed to it by the search form.
    consortium = StringField('Consortium')

    # Donor ID. This field will be populated by the edit route, based on information passed to it by the search form.
    donorid = StringField('Donor ID')

    # Age requires both a value and a selection of unit.
    ageunits = valuesetmanager.getvaluesettuple(tab='Age', group_term='Age', col='units')
    ageunit = SelectField('units', choices=ageunits)

    # Apr 2025 remove rounding (places=1).
    # agevalue = DecimalField('Age (value)',places=1, validators=[validate_age])
    #agevalue = DecimalField('Age (value)', validators=[validate_age])
    agevalue = StringField('Age (value)', validators=[validate_age])
    # Race
    races = valuesetmanager.getvaluesettuple(tab='Race', group_term='Race')
    race = SelectField('Race', choices=races)

    # Ethnicity
    ethnicities = valuesetmanager.getvaluesettuple(tab='Ethnicity', group_term='Ethnicity', addprompt=True)
    ethnicity = SelectField('Ethnicity', choices=ethnicities)

    # Sex
    sexes = valuesetmanager.getvaluesettuple(tab='Sex', group_term='Sex')
    sex = SelectField('Sex', choices=sexes)

    # Source name
    sources = [('0', 'living_donor_data'), ('1', 'organ_donor_data'), ('PROMPT', 'Select an option')]
    source = SelectField('Source name', choices=sources, validators=[validate_required_selectfield])

    # Cause of Death
    causes = valuesetmanager.getvaluesettuple(tab='Cause of Death', group_term='Cause of Death', addprompt=True)
    cause = SelectField('Cause of Death', choices=causes, validators=[validate_selectfield_default])

    # Mechanism of Injury
    mechanisms = valuesetmanager.getvaluesettuple(tab='Mechanism of Injury', group_term='Mechanism of Injury',
                                                  addprompt=True)
    mechanism = SelectField('Mechanism of Injury', choices=mechanisms, validators=[validate_selectfield_default])

    # Death Event
    events = valuesetmanager.getvaluesettuple(tab='Death Event', group_term='Death Event', addprompt=True)
    event = SelectField('Death Event', choices=events, validators=[validate_selectfield_default])

    # Measurements
    # Create SelectFields for each measurement group.
    heightvalue = DecimalField('Height (value)', validators=[validators.Optional()])
    heightunit = SelectField('units', choices=[('0', 'cm'), ('1', 'in')], validators=[validators.Optional()])
    weightvalue = DecimalField('Weight (value)', validators=[validators.Optional()])
    weightunit = SelectField('units', choices=[('0', 'kg'), ('1', 'lb')], validators=[validators.Optional()])
    bmi = DecimalField('Body Mass Index (kg/m2)', validators=[validators.Optional()])
    waistvalue = DecimalField('Waist circumference', validators=[validators.Optional()])
    waistunit = SelectField('units', choices=[('0', 'cm'), ('1', 'in')], validators=[validators.Optional()])
    kdpi = DecimalField('KDPI (%)', validators=[validators.Optional()])
    hba1c = DecimalField('HbA1c (%)', validators=[validators.Optional()])
    amylase = DecimalField('Amylase (U/L)', validators=[validators.Optional()])
    lipase = DecimalField('Lipase (U/L)', validators=[validators.Optional()])
    egfr = DecimalField('eGFR (mL/min/1.73m2)', validators=[validators.Optional()])
    secr = DecimalField('Creatinine (mg/dL)', validators=[validators.Optional()])
    agemenarche = DecimalField('Age at menarche (years)', validators=[validators.Optional()])
    agefirstbirth = DecimalField('Age at first birth (years)', validators=[validators.Optional()])
    gestationalage = DecimalField('Gestational age (weeks)', validators=[validators.Optional()])
    cancerrisk = DecimalField('Cancer Risk (%)', validators=[validators.Optional()])
    pathologynote = TextAreaField('Pathology Note', validators=[validators.Optional()])
    apoephenotype = TextAreaField('APOE phenotype', validators=[validators.Optional()])

    # The Fitzpatrick Skin Type, Other Anatomic, blood type, and blood Rh factor are categorical measurements.
    fitz = valuesetmanager.getvaluesettuple(tab='Measurements', group_term="Fitzpatrick Classification Scale",
                                            addprompt=True)
    fitzpatrick = SelectField('Fitzpatrick Scale', choices=fitz,
                              validators=[validate_selectfield_default, validators.Optional()])

    other_anatomics = valuesetmanager.getvaluesettuple(tab='Measurements', group_term="Other Anatomic Concept",
                                            addprompt=True)
    other_anatomic = SelectField('Other Anatomic', choices=other_anatomics,
                              validators=[validate_selectfield_default, validators.Optional()])

    bloodtypes = valuesetmanager.getvaluesettuple(tab='Blood Type', group_term="ABO blood group system",
                                                  addprompt=True)
    bloodtype = SelectField('ABO Blood Type', choices=bloodtypes,
                            validators=[validate_selectfield_default, validators.Optional()])

    bloodrhs = valuesetmanager.getvaluesettuple(tab='Blood Type', group_term="Rh Blood Group",
                                                addprompt=True)
    bloodrh = SelectField('Rh Blood Group', choices=bloodrhs,
                          validators=[validate_selectfield_default, validators.Optional()])

    # Social History fields are categorical; however, the Social History tab uses the same grouping concept,
    # so grouping will need to be manual. The other option of adding distinct grouping concepts would require
    # that we regenerate all donor metadata currently in provenance.

    list_smoking_concepts = ['C0337664', 'C0337672', 'C0337671']
    smokings = valuesetmanager.getvaluesettuple(tab='Social History', list_concepts=list_smoking_concepts,
                                                addprompt=True)
    smoking = SelectField('Smoking history', choices=smokings,
                          validators=[validate_selectfield_default, validators.Optional()])

    tobaccos = valuesetmanager.getvaluesettuple(tab='Social History', list_concepts=['C3853727'],
                                                addprompt=True)
    tobacco = SelectField('Tobacco history', choices=tobaccos,
                          validators=[validate_selectfield_default, validators.Optional()])

    list_alcohol_concepts = ['C0001948', 'C0457801', 'C0001969']
    alcohols = valuesetmanager.getvaluesettuple(tab='Social History', list_concepts=list_alcohol_concepts,
                                                addprompt=True)
    alcohol = SelectField('Alcohol history', choices=alcohols,
                          validators=[validate_selectfield_default, validators.Optional()])

    list_drug_concepts = ['C4518790', 'C0524662', 'C0242566', 'C1456624', 'C3266350', 'C0281875',
                          'C0013146', 'C0239076']
    drugs = valuesetmanager.getvaluesettuple(tab='Social History', list_concepts=list_drug_concepts,
                                             addprompt=True)

    # Allow for multiple "other drug" use.
    drug_0 = SelectField('Other drug history', choices=drugs,
                       validators=[validate_selectfield_default, validators.Optional()])
    drug_1 = SelectField('Other drug history', choices=drugs,
                         validators=[validate_selectfield_default, validators.Optional()])
    drug_2 = SelectField('Other drug history', choices=drugs,
                         validators=[validate_selectfield_default, validators.Optional()])

    # Medical History
    # A fixed set of medical history fields will be instantiated. Assume a maximum of 10 conditions.
    # Because of the requirement to set the choices using the valuesetmanager, the FieldList methodology cannot
    # be used.
    medhx = valuesetmanager.getvaluesettuple(tab='Medical History', group_term='Medical History', addprompt=True)
    medhx_0 = SelectField('Condition 1', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_1 = SelectField('Condition 2', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_2 = SelectField('Condition 3', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_3 = SelectField('Condition 4', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_4 = SelectField('Condition 5', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_5 = SelectField('Condition 6', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_6 = SelectField('Condition 7', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_7 = SelectField('Condition 8', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_8 = SelectField('Condition 9', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_9 = SelectField('Condition 10', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_10 = SelectField('Condition 11', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_11 = SelectField('Condition 12', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_12 = SelectField('Condition 13', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_13 = SelectField('Condition 14', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_14 = SelectField('Condition 15', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_15 = SelectField('Condition 16', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_16 = SelectField('Condition 17', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_17 = SelectField('Condition 18', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_18 = SelectField('Condition 19', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])
    medhx_19 = SelectField('Condition 20', choices=medhx,
                           validators=[validate_selectfield_default, validators.Optional()])

    # March 2025
    # Pregnancy
    gravida = DecimalField('Gravida', validators=[validators.Optional()])
    parity = DecimalField('Parity', validators=[validators.Optional()])
    abortus = DecimalField('Abortus', validators=[validators.Optional()])

    review = SubmitField()
