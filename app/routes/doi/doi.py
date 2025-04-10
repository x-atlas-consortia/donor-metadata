"""
Routes for comparing donor clinical metadata with DOI titles for
associated published datasets.

April 2025

"""

from flask import Blueprint, request, redirect, render_template, session, make_response, flash


# Helper classes
from models.doiform import DOIForm
from models.searchapi import SearchAPI
from models.getdoistartandend import getdoistartandend
from models.setinputdisabled import setinputdisabled

doi_select_blueprint = Blueprint('doi_select', __name__, url_prefix='/doi/select')

@doi_select_blueprint.route('', methods=['GET','POST'])
def doi_select():

    # Load form that allows for specification of the consortium for which a complete set of donor metadata will be
    # exported.

    form = DOIForm(request.form)
    tstartandend = getdoistartandend()
    form.start.data = tstartandend[0]
    form.batch.data = tstartandend[1]
    setinputdisabled(form.start, disabled=True)
    setinputdisabled(form.batch, disabled=True)

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    if request.method == 'POST' and form.validate():
        # Pass the Globus environment to which to authenticate.
        session['consortium'] = form.consortium.data
        # Indicate to the Globus auth that this is for DOI comparison of all donors in the consortium.
        session['donorid'] = 'DOI'

        # Authenticate to Globus via the login route.
        # If login is successful, Globus will redirect to the hidden DOI review page.
        return redirect(f'/login')

    # Render the export selection form.
    return render_template('doi_select.html', form=form)


doi_review_blueprint = Blueprint('doi_review', __name__, url_prefix='/doi/review')

@doi_review_blueprint.route('', methods=['GET'])
def doi_review():

    # Redirected from the Globus authorization (the /login route in the auth path), which
    # was invoked by the doi_select function.

    # The DOI review page builds an export dataset for a batch of donors and
    # exports to a CSV file. The page does not display.

    # Obtain all donor metadata for a consortium.
    consortium = session['consortium']
    token = session['groups_token']

    # Because of the risk of timeout, process only a batch of donors at a time.
    tstartend = getdoistartandend()
    start = tstartend[0]
    end = tstartend[1]

    # Get DataFrame of metadata rows.
    s = SearchAPI(consortium=consortium, token=token)
    # Use the base metadata dataframe to build a dataframe of DOI-related metadata.
    # It would be possible to build the DOI metadata dataset more directly; however, the
    # detailed parsing would be similar to just pulling it from the standard dataset of
    # donor metadata developed for the original purpose of the application,
    # which runs quickly.
    dfexportmetadata = s.getalldonordoimetadata(start=start, end=end)
    sep = ','
    export_string = dfexportmetadata.to_csv(index=False, sep=sep)

    # Create a response with the exported data.
    response = make_response(export_string)
    response.headers["Content-Disposition"] = f"attachment; filename={consortium.split('_')[1]}_doi_metadata_{start}_{end}.csv"
    response.headers["Content-Type"] = f"text/{format}"

    return response

