"""
Globus environment selection
"""

from flask import Blueprint, request, render_template, redirect, session, abort, url_for

# Helper classes
from models.appconfig import AppConfig
from models.globusform import GlobusForm

globus_blueprint = Blueprint('globus', __name__, url_prefix='/')
@globus_blueprint.route('', methods=['GET', 'POST'])
def globus():

    form = GlobusForm(request.form)
    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    if request.method == 'POST' and form.validate():
        # Obtain the Globus environment to which to authenticate.
        session['consortium'] = form.consortium.data

        return redirect('/login')

    return render_template('index.html', form=form)

