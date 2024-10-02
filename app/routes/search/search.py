"""
Donor search page
This is the initial page in the curation workflow.
Works with searchform.py.

Allows the user to specify the consortium and donor.

"""
from flask import Blueprint, request, render_template, redirect, session

# Helper classes
# The form used to execute a GET request against the entity-api of a consortium
from models.searchform import SearchForm
# Represents metadata for a donor in a provenance database of a consortium.
from models.donor import DonorData

search_blueprint = Blueprint('search', __name__, url_prefix='/')


@search_blueprint.route('', methods=['GET', 'POST'])
def search():

    form = SearchForm(request.form)
    if request.method == 'GET':
        # Obtain the authentication token from the session cookie.
        if 'HMSNDonortoken' in session:
            form.token.data = session['HMSNDonortoken']

    if request.method == 'POST' and form.validate():

        # Query the provenance database of the specified consortium to validate that the specified
        # donor currently exists.

        donorid = form.donorid.data

        # Write the token to a session cookie.
        if 'HMSNDonortoken' in session:
            session.pop('HMSNDonortoken', None)
        session['HMSNDonortoken'] = form.token.data

        # Attempt to load metadata for the donor. The load will abort if unable to load data.
        token = session['HMSNDonortoken']
        currentdonordata = DonorData(donorid=donorid, token=token)

        # Clear messages related to prior updates.
        if 'flashes' in session:
            session['flashes'].clear()

        # Load the edit form for the donor. Use redirect and pass the donorid via GET. The Edit form populates
        # itself by reading donor metadata from provenance.
        return redirect(f'/edit/{donorid}')

    return render_template('index.html', form=form)
