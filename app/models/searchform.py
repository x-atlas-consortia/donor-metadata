"""
Form used to search for a donor by ID in the provenance database of a consortium.
"""

import os

from wtforms import Form, validators, ValidationError, SelectField, StringField
from .appconfig import AppConfig

def validate_donorid(form, field):
    """
    Custom validator.
    Checks whether the first three characters of the id correspond to the selected context.
    :param form: the EditForm
    :param field: the donorid field
    :return: Nothing or raises ValidationError

    """
    idcontext = field.data.split('.')[0][0:3].upper()

    # Compare against the selected value of context.
    if idcontext == 'HBM':
        if form.context.data != 'CONTEXT_HUBMAP':
            raise ValidationError('HuBMAP IDs must begin with HMB.')
    elif idcontext == 'SNT':
        if form.context.data != 'CONTEXT_SENNET':
            raise ValidationError('SenNet IDs must begin with SNT.')
    else:
        raise ValidationError(f'Unknown ID prefix {idcontext}')


class SearchForm(Form):

    # POPULATE FORM FIELDS. In particular, populate SelectFields with lists obtained from the valueset manager.

    # Read the app.cfg file outside the Flask application context.
    fpath = os.path.dirname(os.getcwd())
    fpath = os.path.join(fpath, 'app/instance/app.cfg')
    cfg = AppConfig()

    # Obtain the Globus token from app.cfg. This should correspond to the globus auth token in the application
    # context.
    token = cfg.getfield(key='GLOBUS_TOKEN').replace("'", "")

    # Application context for entity-api URLs (HuBMAP or SenNet).
    # This field will be used to build the appropriate endpoint URL.
    contexts = cfg.getfieldlist(prefix='CONTEXT_')
    context = SelectField('Consortium', choices=contexts)

    # Donor ID. This should be validated for format (i.e., contains expected delimiters) and
    # that the first two characters of the ID match the application context (e.g., HM and hubmapconsortium.org).
    message = 'ID format: CCCnnn.XXXX.nnn: <CCC> either HBM or SNT; <n> integer; <X> non-numeric'
    regex = '[^0-9]{3}[0-9]{3}\.[^0-9]{4}\.[0-9]{3}'
    donorid = StringField('Donor ID', validators=[validators.DataRequired(),
                                                  validators.regexp(regex=regex, message=message),
                                                  validate_donorid])


