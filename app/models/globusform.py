"""
Form used to log a user into a consortium's Globus environment.
First form in the curation workflow.
"""

from wtforms import Form, validators, ValidationError, SelectField, StringField, PasswordField
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

    if idcontext == 'HBM':
        if form.consortium.data != 'CONTEXT_HUBMAP':
            raise ValidationError('Incorrect consortium for donor ID.')
    elif idcontext == 'SNT':
        if form.consortium.data != 'CONTEXT_SENNET':
            raise ValidationError('Incorrect consortium for donor ID.')
    else:
        raise ValidationError(f'Unknown ID prefix {idcontext}')

class GlobusForm(Form):

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Application context for entity-api URLs, corresponding to a consortium.
    # This field will be used to build the appropriate endpoint URL.
    consortia = cfg.getfieldlist(prefix='CONTEXT_')
    consortium = SelectField('Globus Consortium', choices=consortia)

    # Donor ID. This should be validated for format (i.e., contains expected delimiters) and
    # that the first two characters of the ID match the consortium:
    # HBM and hubmapconsortium.org
    # SNT and sennetconsortium.org

    message = 'ID format: CCCnnn.XXXX.nnn: <CCC> either HBM or SNT; <n> integer; <X> non-numeric'
    regex = '[^0-9]{3}[0-9]{3}\.[^0-9]{4}\.[0-9]{3}'
    donorid = StringField('Donor ID', validators=[validators.DataRequired(),
                                                  validators.regexp(regex=regex, message=message),
                                                  validate_donorid])

    # Clear validation errors. This handles the common use case in which the user returns to the search form after
    # seeing a 4XX error.
    donorid.errors = []
    consortium.errors = []

