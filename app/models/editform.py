"""
Form used to build the request body of the POST (create) or PUT (update) endpoints for the HuBMAP and SenNet
entity-api.
"""
import os

from wtforms import (Form, StringField, SelectField, DecimalField, validators, ValidationError,
                     FieldList, FormField, TextAreaField, SelectMultipleField)
from flask_wtf import FlaskForm

from .appconfig import AppConfig
from .valuesetmanager import ValueSetManager


# ---- CUSTOM VALIDATORS
def validate_donorid(form, field):
    """
    Checks whether the first three characters of the id correspond to the selected context.
    :param form: the EditForm
    :param field: the donorid field
    :return: Nothing or raises ValidationError

    """
    idcontext = field.data.split('.')[0][0:2].upper()

    # Compare against the selected value of context.
    if idcontext == 'HM':
        if form.context.data != 'CONTEXT_HUBMAP':
            raise ValidationError('HuBMAP IDs must begin with HM.')
    elif idcontext == 'SN':
        if form.context.data != 'CONTEXT_SENNET':
            raise ValidationError('SenNet IDs must begin with SN.')
    else:
        raise ValidationError(f'Unknown ID prefix {idcontext}')


def validate_age(form, field):
    """
    Checks that age is at least 1 month.

    :param form: the Edit form
    :param field: the age field
    :return: Nothing or raises ValidationError
    """

    ageunit = form.ageunit.data
    age = field.data

    if age == 0:
        raise ValidationError('The minimum age is 1 month.')
    if age > 89 and ageunit == 'C0001779':  # UMLS CUI for age in years
        raise ValidationError('All ages over 89 years must be set to 90 years.')

# ----------------------
# MAIN FORM
class EditForm(Form):

    # POPULATE FORM FIELDS WITH SELECTION OPTIONS.

    # Read the app.cfg file outside the Flask application context.
    fpath = os.path.dirname(os.getcwd())
    fpath = os.path.join(fpath, 'app/instance/app.cfg')
    cfg = AppConfig()

    # Instantiate the ValuesetManager that reads resources for form controls from a
    # Google Sheet.
    # Get URL to Google sheet, with single quote literals stripped.
    url = cfg.getfield(key='VALUESETMANAGER').replace("'", "")
    # Export path for valueset spreadsheet.
    fpath = os.path.join(os.path.dirname(os.getcwd()), 'app/valueset/valuesets.xlsx')
    # Download current version of valueset data.
    valuesetmanager = ValueSetManager(url=url, download_full_path=fpath)

    # Application context for entity-api URLs (HuBMAP or SenNet).
    # This field will be used to build the appropriate endpoint URL.
    contexts = cfg.getfieldlist(prefix='CONTEXT_')
    context = SelectField('Consortium', choices=contexts)

    # Donor ID. This should be validated for format (i.e., contains expected delimiters) and
    # that the first two characters of the ID match the application context (e.g., HM and hubmapconsortium.org).
    donorid = StringField('Donor ID', validators=[validators.DataRequired(),
                                                  validators.regexp('\D\D\d\d\d\.\D\D\D\.\d\d\d',
                                                                    message='ID format: CCnnn.XXX.nnn, with '
                                                                            'CC either HM or SN; n integer;'
                                                                            'X non-numeric'),validate_donorid])

    # Source_name is not encoded as a valueset, so hard-code the selection.
    source_name = SelectField('Source name', choices=[('0', 'living_donor_data'), ('1', 'organ_donor_data'),('PROMPT','Select an option')])

    # Age requires both a value and a selection of unit.

    ageunits = valuesetmanager.getValuesetTuple(tab='Age', col=''
                                                               'units')
    ageunit = SelectField('units', choices=ageunits)
    agevalue = DecimalField('Age (value)', validators=[validators.DataRequired(), validate_age])

    # Race
    races = valuesetmanager.getValuesetTuple(tab='Race')
    race = SelectField('Race', choices=races)

    # Ethnicity
    ethnicities = valuesetmanager.getValuesetTuple(tab='Ethnicity', addprompt=True)
    ethnicity = SelectField('Ethnicity', choices=ethnicities)

    # Sex
    sexes = valuesetmanager.getValuesetTuple(tab='Sex')
    sex = SelectField('Sex', choices=sexes)

    # Cause of Death
    causes = valuesetmanager.getValuesetTuple(tab='Cause of Death', addprompt=True)
    cause = SelectField('Cause of Death', choices=causes)

    # Mechanism of Injury
    mechanisms = valuesetmanager.getValuesetTuple(tab='Mechanism of Injury', addprompt=True)
    mechanism = SelectField('Mechanism of Injury', choices=mechanisms)

    # Death Event
    events = valuesetmanager.getValuesetTuple(tab='Death Event', addprompt=True)
    event = SelectField('Death Event', choices=events)

    # Measurements
    # Create SelectFields for each measurment group.
    heightvalue = DecimalField('Height (value)')
    heightunit = SelectField('units', choices=[('0','cm'),('1','in')])
    weightvalue = DecimalField('Weight (value)')
    weightunit = SelectField('units', choices=[('0', 'kg'), ('1', 'lb')])
    bmi = DecimalField('Body Mass Index (kg/m^2)')
    waistvalue = DecimalField('Waist circumference')
    waistunit = SelectField('units', choices=[('0','cm'),('1','in')])
    kdpi = DecimalField('Kidney donor profile index (%)')
    hba1c = DecimalField('HbA1c (%)')
    amylase = DecimalField('Amylase (IU)')
    lipase = DecimalField('Lipase (IU)')
    agemenarche = DecimalField('Age at menarche (years)')
    agefirstbirth = DecimalField('Age at first birth (years)')
    gestationalage = DecimalField('Gestational age (weeks)')
    cancerrisk = DecimalField('Cancer Risk (%)')
    pathologynote=TextAreaField('Pathology Note')
    apoephenotype=TextAreaField('APOE phenotype')

    # The Fitzpatrick Skin Type, blood type, and blood Rh factor are categorical measurements.
    fitz = valuesetmanager.getValuesetTuple(tab='Measurements',group_term="Fitzpatrick Classification Scale",
                                                  addprompt=True)
    fitzpatrick = SelectField('Fitzpatrick Classification Scale', choices=fitz)

    bloodtypes = valuesetmanager.getValuesetTuple(tab='Blood Type', group_term="ABO blood group system",
                                            addprompt=True)
    bloodtype = SelectField('ABO Blood Type', choices=bloodtypes)

    bloodrhs = valuesetmanager.getValuesetTuple(tab='Blood Type', group_term="Rh Blood Group",
                                                  addprompt=True)
    bloodrh = SelectField('Rh Blood Group', choices=bloodrhs)

    # Social History fields are categorical; however, the Social History tab uses the same grouping concept,
    # so grouping will need to be manual. The other option of adding distinct grouping concepts would require
    # that we regenerate all donor metadata currently in provenance.

    list_smoking_concepts = ['C0337664','C0337672', 'C0337671']
    smokings = valuesetmanager.getValuesetTuple(tab='Social History', list_concepts=list_smoking_concepts,
                                               addprompt=True)
    smoking = SelectField('Smoking history', choices=smokings)

    tobaccos = valuesetmanager.getValuesetTuple(tab='Social History', list_concepts=['C3853727'], addprompt=True)
    tobacco = SelectField('Tobacco history', choices=tobaccos)

    list_alcohol_concepts = ['C0001948', 'C0457801']
    alcohols = valuesetmanager.getValuesetTuple(tab='Social History', list_concepts=list_alcohol_concepts, addprompt=True)
    alcohol = SelectField('Alcohol history', choices=alcohols)

    list_drug_concepts = ['C4518790','C0524662','C0242566','C1456624','C3266350','C0281875','C0013146','C0239076']
    drugs = valuesetmanager.getValuesetTuple(tab='Social History', list_concepts=list_drug_concepts,
                                                addprompt=True)
    drug = SelectField('Other drug history', choices=drugs)

    # Medical History
    # A fixed set of medical history fields will be instantiated. Assume a maximum of 10 conditions.
    # Because of the requirement to set the choices using the valuesetmanager, the FieldList methodology cannot
    # be used.
    medhx = valuesetmanager.getValuesetTuple(tab='Medical History', addprompt=True)
    medhx_0 = SelectField('Condition', choices=medhx)
    medhx_1 = SelectField('Condition', choices=medhx)
    medhx_2 = SelectField('Condition', choices=medhx)
    medhx_3 = SelectField('Condition', choices=medhx)
    medhx_4 = SelectField('Condition', choices=medhx)
    medhx_5 = SelectField('Condition', choices=medhx)
    medhx_6 = SelectField('Condition', choices=medhx)
    medhx_7 = SelectField('Condition', choices=medhx)
    medhx_8 = SelectField('Condition', choices=medhx)
    medhx_9 = SelectField('Condition', choices=medhx)
    medhx_10 = SelectField('Condition', choices=medhx)


