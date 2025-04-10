"""
Routes for the metadata export workflows.

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

    # Load form that allows for specification of the consortium for which a complete set of donor metadata will be
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

    donorid = session['donorid']

    if donorid == 'ALL':
        # Obtain all donor metadata for a consortium.
        # Populate review form with consortium donor metadata.
        consortium = session['consortium']
        token = session['groups_token']

        # Get DataFrame of metadata rows.
        dfexportmetadata = SearchAPI(consortium=consortium, token=token).dfalldonormetadata
    else:
        # Obtain and decode the base64-encoded dictionary of new donor metadata,
        # which is stored in the session cookie.
        newdonorb64 = session['newdonortsv']
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

    if request.method == 'GET':
        # Redirected from the Globus authorization (the /login route in the auth path).
        # Convert to HTML table.
        table = dfexportmetadata.to_html(classes='table table-hover .table-condensed { font-size: 8px !important; } '
                                                  'table-bordered table-responsive-sm')

    if request.method == 'POST':
        # Export the export review form content, indicated by the value of the clicked button in the form.
        format = request.form.getlist('export')[0]
        if format == 'csv':
            sep = ','
        else:
            sep = '\t'
        export_string = dfexportmetadata.to_csv(index=False, sep=sep)

        # Create a response with the exported data
        response = make_response(export_string)
        if donorid == 'ALL':
            fname = consortium.split('_')[1].lower()
        else:
            fname = donorid
        response.headers["Content-Disposition"] = f"attachment; filename={fname}_metadata.{format}"
        response.headers["Content-Type"] = f"text/{format}"
        flash(f'Metadata for {fname} exported.')
        return response

    return render_template('export_review.html', table=table)


export_donor_blueprint = Blueprint('export_tsv_review_new', __name__, url_prefix='/export/donor')

@export_donor_blueprint.route('', methods=['POST'])
def export_donor():
    # Pass data from the donor review page to the common export review page.
    session['newdonortsv'] = request.form.getlist('newdonortsv')
    return redirect(f'/export/review')


