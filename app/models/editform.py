"""
Form used to build the JSON of new metadata for a donor in provenance.
Second form in the workflow.
"""
import os

from wtforms import (Form, StringField, SelectField, DecimalField, validators, ValidationError,
                     TextAreaField, SubmitField)

# Helper classes
# Represents the app.cfg file
from .appconfig import AppConfig
# Represents the Google Sheets of donor clinical metadata valuesets
from .valuesetmanager import ValueSetManager


def validate_age(form, field):
    """
    Custom validator. Checks that age is at least 1 month.

    :param form: the Edit form
    :param field: the age field
    :return: Nothing or raises ValidationError
    """

    ageunit = form.ageunit.data
    age = field.data

    if age <= 0:
        raise ValidationError('The minimum age is 1 month.')
    if age > 89 and ageunit == 'C0001779':  # UMLS CUI for age in years
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
    fpath = os.path.join(os.path.dirname(os.getcwd()), 'app/valueset/valuesets.xlsx')
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
    agevalue = DecimalField('Age (value)',
                            validators=[validators.DataRequired(), validators.NumberRange(min=0), validate_age])

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
    # Create SelectFields for each measurment group.
    heightvalue = DecimalField('Height (value)', validators=[validators.Optional()])
    heightunit = SelectField('units', choices=[('0', 'cm'), ('1', 'in')], validators=[validators.Optional()])
    weightvalue = DecimalField('Weight (value)', validators=[validators.Optional()])
    weightunit = SelectField('units', choices=[('0', 'kg'), ('1', 'lb')], validators=[validators.Optional()])
    bmi = DecimalField('Body Mass Index (kg/m^2)', validators=[validators.Optional()])
    waistvalue = DecimalField('Waist circumference', validators=[validators.Optional()])
    waistunit = SelectField('units', choices=[('0', 'cm'), ('1', 'in')], validators=[validators.Optional()])
    kdpi = DecimalField('KDPI (%)', validators=[validators.Optional()])
    hba1c = DecimalField('HbA1c (%)', validators=[validators.Optional()])
    amylase = DecimalField('Amylase (IU)', validators=[validators.Optional()])
    lipase = DecimalField('Lipase (IU)', validators=[validators.Optional()])
    egfr = DecimalField('eGFR (mL/min/1.73m^2)', validators=[validators.Optional()])
    secr = DecimalField('Creatinine (mg/dL)', validators=[validators.Optional()])
    agemenarche = DecimalField('Age at menarche (years)', validators=[validators.Optional()])
    agefirstbirth = DecimalField('Age at first birth (years)', validators=[validators.Optional()])
    gestationalage = DecimalField('Gestational age (weeks)', validators=[validators.Optional()])
    cancerrisk = DecimalField('Cancer Risk (%)', validators=[validators.Optional()])
    pathologynote = TextAreaField('Pathology Note', validators=[validators.Optional()])
    apoephenotype = TextAreaField('APOE phenotype', validators=[validators.Optional()])

    # The Fitzpatrick Skin Type, blood type, and blood Rh factor are categorical measurements.
    fitz = valuesetmanager.getvaluesettuple(tab='Measurements', group_term="Fitzpatrick Classification Scale",
                                            addprompt=True)
    fitzpatrick = SelectField('Fitzpatrick Scale', choices=fitz,
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

    list_alcohol_concepts = ['C0001948', 'C0457801']
    alcohols = valuesetmanager.getvaluesettuple(tab='Social History', list_concepts=list_alcohol_concepts,
                                                addprompt=True)
    alcohol = SelectField('Alcohol history', choices=alcohols,
                          validators=[validate_selectfield_default, validators.Optional()])

    list_drug_concepts = ['C4518790', 'C0524662', 'C0242566', 'C1456624', 'C3266350', 'C0281875',
                          'C0013146', 'C0239076']
    drugs = valuesetmanager.getvaluesettuple(tab='Social History', list_concepts=list_drug_concepts,
                                             addprompt=True)
    drug = SelectField('Other drug history', choices=drugs,
                       validators=[validate_selectfield_default, validators.Optional()])

    # Medical History
    # A fixed set of medical history fields will be instantiated. Assume a maximum of 10 conditions.
    # Because of the requirement to set the choices using the valuesetmanager, the FieldList methodology cannot
    # be used.
    medhx = valuesetmanager.getvaluesettuple(tab='Medical History', group_term='Medical History', addprompt=True)
    medhx_0 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_1 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_2 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_3 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_4 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_5 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_6 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_7 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_8 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])
    medhx_9 = SelectField('Condition', choices=medhx,
                          validators=[validate_selectfield_default, validators.Optional()])

    review = SubmitField()
