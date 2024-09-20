"""
Donor metadata curation review and update page
Third form in the curation workflow.

Does the following:
1. Compares the existing metadata for a donor with the proposed changes to the metadata.
2. If there are any changes to the metadata, allows the user to submit a request to update metadata for the
   donor in provenance.
"""

from flask import Blueprint, request, render_template, redirect

update_blueprint = Blueprint('update', __name__, url_prefix='/update')

@update_blueprint.route('', methods=['GET', 'POST'])
def edit():


    if request.method == 'POST':# and form.validate():
        # Translate revised donor metadata fields into the encoded donor metadata schema.
        form.newdonordata = buildnewdonordata(form)
        # Return to the
        #return render_template('search.html', form=form)

    return render_template('update.html', form=form)
