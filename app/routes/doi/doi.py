"""
Routes for comparing donor clinical metadata with DOI titles for
associated published datasets.

April 2025

"""

from flask import Blueprint, request, redirect, render_template, session, make_response, flash

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


@doi_review_blueprint.route('', methods=['POST', 'GET'])
def doi_review():

    # Obtain all donor metadata for a consortium.
    # Populate review form with consortium donor metadata.
    consortium = session['consortium']
    token = session['groups_token']

    # Get DataFrame of metadata rows.
    search = SearchAPI(consortium=consortium, token=token)
    dfexportmetadata = search.getalldonordoimetadata()

    if request.method == 'GET':
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
        fname = consortium.split('_')[1].lower()

        response.headers["Content-Disposition"] = f"attachment; filename={fname}_metadata.{format}"
        response.headers["Content-Type"] = f"text/{format}"
        flash(f'Metadata for {fname} exported.')
        return response

    return render_template('doi_review.html', table=table)
