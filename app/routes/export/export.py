"""
Routes for the metadata export workflow.

"""

from flask import Blueprint, request, redirect, render_template, session, make_response, flash, abort
import pickle
import base64
import pandas as pd

# Helper classes
from models.exportform import ExportForm
from models.searchapi import SearchAPI

export_select_blueprint = Blueprint('export_select', __name__, url_prefix='/export/select')


@export_select_blueprint.route('', methods=['GET', 'POST'])
def export_select():

    # Load form that allows for specification of the consortium for which the set of donor metadata will be
    # exported.

    form = ExportForm(request.form)

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    if request.method == 'POST' and form.validate():
        # Pass the Globus environment to which to authenticate.
        session['consortium'] = form.consortium.data
        # Indicate to the Globus auth that this is for all donors in the consortium.
        session['donorid'] = 'ALL'
        # Authenticate to Globus via the login route.
        # If login is successful, Globus will redirect to the export review page.
        return redirect(f'/login')

    # Render the export selection form.
    return render_template('export_select.html', form=form)


export_review_blueprint = Blueprint('export_review', __name__, url_prefix='/export/review')


@export_review_blueprint.route('', methods=['POST', 'GET'])
def export_review():

    # Obtains all donor metadata for a consortium.
    # Sends metadata to export review form as a Pandas DataFrame for display.

    # Populate review form with consortium donor metadata.
    consortium = session['consortium']
    token = session['groups_token']

    # Get DataFrame of metadata rows.
    exportmetadata = SearchAPI(consortium=consortium, token=token).metadata

    if request.method == 'GET':
        # Remove irrelevant columns for display purposes.
        metadatadisplay = exportmetadata[['id', 'source_name',
                                                    'code', 'concept_id',
                                                    'data_type', 'data_value',
                                                    'grouping_code', 'grouping_concept',
                                                    'grouping_concept_preferred_term',
                                                    'grouping_sab', 'numeric_operator',
                                                    'preferred_term', 'sab', 'units']]
        # Convert to HTML table.
        table = metadatadisplay.to_html(classes='table table-hover .table-condensed { font-size: 8px !important; } '
                                                'table-bordered table-responsive-sm')

    if request.method == 'POST':
        # Export form content to excel.
        csv_string = exportmetadata.to_csv(index=False)
        # Create a response with the CSV data
        response = make_response(csv_string)
        fname = consortium.split('_')[1].lower()
        response.headers["Content-Disposition"] = f"attachment; filename={fname}_metadata.csv"
        response.headers["Content-Type"] = "text/csv"
        flash(f'Metadata for {fname} exported.')
        return response

    return render_template('export_review.html', table=table)


export_tsv_blueprint = Blueprint('export_tsv', __name__, url_prefix='/export/tsv')


@export_tsv_blueprint.route('', methods=['POST', 'GET'])
def export_tsv():

    # Obtain and decode the base64-encoded dictionary of new donor metadata,
    # which is stored in a hidden input in the second form in review.html.
    newdonorb64 = request.form.getlist('newdonortsv')
    if len(newdonorb64) > 0:
        newdonor = pickle.loads(base64.b64decode(newdonorb64[0]))  # Decoded back to dictionary
    else:
        abort(400, 'No new metadata')
        # Remove irrelevant columns for display purposes.
    print(newdonor)
    metadata = pd.DataFrame([newdonor])
    metadata = df_for_display(df=metadata)
    # Convert to HTML table.
    table = metadata.to_html(
        classes='table table-hover .table-condensed { font-size: 8px !important; } table-bordered table-responsive-sm')

    return render_template('export_review.html', table=table)
