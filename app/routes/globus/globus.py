"""
Index route that:
1. obtains Globus environment and donor id from a WTForm (GlobusForm)
2. authenticates to Globus
"""

from flask import Blueprint, request, render_template, redirect, session

# Helper classes
from models.globusform import GlobusForm

globus_blueprint = Blueprint('globus', __name__, url_prefix='/')


@globus_blueprint.route('', methods=['GET', 'POST'])
def globus():

    form = GlobusForm(request.form)

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    if request.method == 'POST' and form.validate():
        # Pass the Globus environment to which to authenticate.
        session['consortium'] = form.consortium.data
        # Pass the donor id.
        session['donorid'] = form.donorid.data
        # Authenticate to Globus via the login route.
        return redirect(f'/login')

    # Render the Globus login form.
    return render_template('index.html', form=form)
