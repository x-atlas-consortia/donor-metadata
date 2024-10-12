"""
Form used to log a user into a consortium's Globus environment.
First form in the workflow.
"""

import os

from wtforms import Form, validators, ValidationError, SelectField, StringField, PasswordField
from .appconfig import AppConfig

class GlobusForm(Form):

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Application context for entity-api URLs, corresponding to a consortium.
    # This field will be used to build the appropriate endpoint URL.
    consortia = cfg.getfieldlist(prefix='CONTEXT_')
    consortium = SelectField('Consortium', choices=consortia)

