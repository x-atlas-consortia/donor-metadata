"""
Routes for the metadata export workflow.

"""

from flask import Blueprint, request, redirect, render_template, session, make_response, flash, abort, send_file
import pickle
import base64

# Helper classes
from models.exportform import ExportForm
from models.searchapi import SearchAPI
from models.metadataframe import MetadataFrame
from models.getmetadatabytype import getmetadatabytype

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
    dfexportmetadata = SearchAPI(consortium=consortium, token=token).dfalldonormetata

    if request.method == 'GET':
        # Remove irrelevant columns for display purposes.
        dfmetadatadisplay = dfexportmetadata[['id', 'source_name',
                                                    'code', 'concept_id',
                                                    'data_type', 'data_value',
                                                    'grouping_code', 'grouping_concept',
                                                    'grouping_concept_preferred_term',
                                                    'grouping_sab', 'numeric_operator',
                                                    'preferred_term', 'sab', 'units']]
        # Convert to HTML table.
        table = dfmetadatadisplay.to_html(classes='table table-hover .table-condensed { font-size: 8px !important; } '
                                                  'table-bordered table-responsive-sm')

    if request.method == 'POST':
        # Export form content to excel.
        csv_string = dfexportmetadata.to_csv(index=False)
        # Create a response with the CSV data
        response = make_response(csv_string)
        fname = consortium.split('_')[1].lower()
        response.headers["Content-Disposition"] = f"attachment; filename={fname}_metadata.csv"
        response.headers["Content-Type"] = "text/csv"
        flash(f'Metadata for {fname} exported.')
        return response

    return render_template('export_review.html', table=table)


export_tsv_blueprint = Blueprint('export_tsv_review_new', __name__, url_prefix='/export/tsv')

@export_tsv_blueprint.route('', methods=['POST','GET'])
def export_tsv():

    # Obtain and decode the base64-encoded dictionary of new donor metadata,
    # which is stored in a hidden input in the second form in review.html.
    newdonorb64 = request.form.getlist('newdonortsv')
    if len(newdonorb64) > 0:
        newdonor = pickle.loads(base64.b64decode(newdonorb64[0]))  # Decoded back to dictionary
    else:
        abort(400, 'No new metadata')

    # Flatten for source_name.
    dfnewdonortype = getmetadatabytype(dictmetadata=newdonor)

    # Flatten for donor id.
    donorid = session['donorid']
    consortium = session['consortium']

    dfexportmetadata = MetadataFrame(metadata=dfnewdonortype, donorid=donorid).dfexport

    # Export new donor metadata to tsv.
    tsv_string = dfexportmetadata.to_csv(index=False,sep='\t')

    # Create a response with the TSV data
    response = make_response(tsv_string)
    # Get the donor ID
    response.headers["Content-Disposition"] = f"attachment; filename={donorid}_metadata.tsv"
    response.headers["Content-Type"] = "text/tsv"
    flash(f'Metadata for {donorid} exported to TSV.')

    return response
