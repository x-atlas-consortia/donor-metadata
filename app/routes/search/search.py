"""
Donor search form
"""
from flask import Blueprint, request, render_template, redirect

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

        # Load the edit form for the donor.
        return redirect(f'/edit/{donorid}')

    return render_template('index.html', form=form)
