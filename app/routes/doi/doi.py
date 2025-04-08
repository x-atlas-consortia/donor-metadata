"""
Routes for comparing donor clinical metadata with DOI titles for
associated published datasets.

April 2025

"""

from flask import Blueprint, request, redirect, render_template, session, make_response, flash
import pickle
import base64
import pandas as pd

# Helper classes
from models.doiform import DOIForm
from models.searchapi import SearchAPI

doi_select_blueprint = Blueprint('doi_select', __name__, url_prefix='/doi/select')


@doi_select_blueprint.route('', methods=['GET', 'POST'])
def doi_select():

    # Load form that allows for specification of the consortium for which a complete set of donor metadata will be
    # exported.

    form = DOIForm(request.form)

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    if request.method == 'POST' and form.validate():
        # Pass the Globus environment to which to authenticate.
        session['consortium'] = form.consortium.data
        # Indicate to the Globus auth that this is for DOI comparison of all donors in the consortium.
        session['donorid'] = 'DOI'

        # Authenticate to Globus via the login route.
        # If login is successful, Globus will redirect to the DOI review page.
        return redirect(f'/login')

    # Render the export selection form.
    return render_template('doi_select.html', form=form)


doi_review_blueprint = Blueprint('doi_review', __name__, url_prefix='/doi/review')


@doi_review_blueprint.route('', methods=['GET','POST'])
def doi_review():

    # Obtain all donor metadata for a consortium.
    # Populate review form with consortium donor metadata.
    consortium = session['consortium']
    token = session['groups_token']

    if request.method == 'GET':
        # Get DataFrame of metadata rows.
        dfexportmetadata = SearchAPI(consortium=consortium, token=token).getalldonordoimetadata()
        print('CONVERTING TO HTML TABLE')
        # Convert to HTML table.
        table = dfexportmetadata.to_html(classes='table table-hover .table-condensed { font-size: 8px !important; } '
                                                 'table-bordered table-responsive-sm')

        # Store the metadata to a session variable for use by the POST method.
        # Convert from a DataFrame to a dictionary, then serialize the dictionary string.
        pickled = base64.b64encode(pickle.dumps(dfexportmetadata.to_dict())).decode()
        session['doiexport'] = pickled

    if request.method == 'POST':
        # Export the export review form content, indicated by the value of the clicked button in the form.
        format = request.form.getlist('export')[0]
        if format == 'csv':
            sep = ','
        else:
            sep = '\t'

        # Obtain and decode the base64-encoded DOI metadata,
        # which was stored in the session cookie by the GET method.
        # Convert to a DataFrame.
        # Write to file.
        doiexport = session['doiexport']
        if len(doiexport) > 0:
            unpickled = pickle.loads(base64.b64decode(doiexport))
            dfexportmetadata = pd.DataFrame(unpickled)
        else:
            abort(400, 'No doi metadata')

        export_string = dfexportmetadata.to_csv(index=False, sep=sep)

        # Create a response with the exported data
        response = make_response(export_string)
        fname = consortium.split('_')[1].lower()
        response.headers["Content-Disposition"] = f"attachment; filename={fname}_metadata.{format}"
        response.headers["Content-Type"] = f"text/{format}"
        flash(f'Metadata for {fname} exported.')
        return response

    return render_template('doi_review.html', table=table)
