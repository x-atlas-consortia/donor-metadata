"""
Form used to select a set of donors to which to compare metadata with DOI titles
for associated datasets.
"""

from wtforms import Form, SelectField, StringField
from models.appconfig import AppConfig


class DOIForm(Form):

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Application context for entity-api URLs, corresponding to a consortium.
    # This field will be used to build the appropriate endpoint URL.
    consortia = cfg.getfieldlist(prefix='CONTEXT_')
    consortium = SelectField('Globus Consortium', choices=consortia)
    start = StringField('Start position in donor list')
    batch = StringField('End position in donor list')

    # Clear validation errors. This handles the common use case in which the user returns to the search form after
    # seeing a 4XX error.
    consortium.errors = []
