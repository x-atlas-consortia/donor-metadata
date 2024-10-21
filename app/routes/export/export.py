"""
Routes for the metadata export workflow.

"""

from flask import Blueprint, request, redirect, render_template, session

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

    if request.method == 'GET':
        # Populate review form with consortium donor metadata.
        consortium = session['consortium']
        token = session['groups_token']

        # Get DataFrame of metadata rows.
        metadata = SearchAPI(consortium=consortium, token=token).metadata
        # Remove irrelevant columns for display purposes.
        metadata = metadata[['id', 'source_name',
                             'code', 'concept_id',
                             'data_type', 'data_value',
                             'grouping_code','grouping_concept',
                             'grouping_concept_preferred_term',
                             'grouping_sab', 'numeric_operator',
                             'preferred_term', 'sab', 'units']]
        table = metadata.to_html(classes='table table-hover .table-condensed { font-size: 8px !important; } table-bordered table-responsive-sm')
        return render_template('export_review.html', table=table)
    if request.method == 'POST':
        # Export form content to excel.
        return redirect('/')

