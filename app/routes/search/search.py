"""
Donor search page
This is the initial page in the curation workflow.
Works with searchform.py.

Allows the user to specify the consortium and donor.

"""
from flask import Blueprint, request, render_template, redirect, session, current_app

# The form used to execute a GET request against the entity-api of a consortium
from models.searchform import SearchForm
# Represents metadata for a donor in a provenance database of a consortium.
from models.donor import DonorData

search_blueprint = Blueprint('search', __name__, url_prefix='/')


@search_blueprint.route('', methods=['GET', 'POST'])
def search():

    form = SearchForm(request.form)

    if request.method == 'POST' and form.validate():

        # Query the provenance database of the specified consortium to validate that the specified
        # donor currently exists.

        # Obtain the value of consortium selected (not the key).
        consortium = dict(form.consortium.choices).get(form.consortium.data)
        donorid = form.donorid.data
        currentDonorData = DonorData(consortium=consortium, donorid=donorid, token=form.token)

        if 'flashes' in session:
            session['flashes'].clear()

        # Load the edit form for the donor. Use redirect and pass the donorid via GET. The Edit form populates
        # itself by reading donor metadata from provenance.
        return redirect(f'/edit/{donorid}')

    return render_template('index.html', form=form)
