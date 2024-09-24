"""
Donor metadata curation review and update page
Final page in the curation workflow.

"""

from flask import Blueprint, request, render_template, redirect, jsonify, abort, flash
import pickle
import base64

# Represents the app.cfg file
from models.appconfig import AppConfig
# Common functions
from models.entity import getconsortiumfromdonorid, updatedonormetadata

review_blueprint = Blueprint('review', __name__, url_prefix='/review')

@review_blueprint.route('', methods=['POST'])
def review():

    # Prepare the call to the PUT entities call in the entity-api.

    # Obtain and decode the base64-encoded dictionary of new donor metadata,
    # which is stored in a hidden input in the form in review.html.
    newdonorb64 = request.form.getlist('newdonor')
    if len(newdonorb64) > 0:
        newdonor = pickle.loads(base64.b64decode(newdonorb64[0]))  # Decoded back to dictionary
    else:
        abort(400, 'No new metadata')

    # Obtain the donor id
    donoridlist = request.form.getlist('donorid')
    if len(donoridlist) > 0:
        donorid = donoridlist[0]
    else:
        abort(400, 'No donorid')

    # Obtain the globus token from the app.cfg file.
    cfg = AppConfig()
    token = cfg.getfield(key='GLOBUS_TOKEN').replace("'", "")
    consortium = getconsortiumfromdonorid(donorid=donorid)
    if updatedonormetadata(consortium=consortium, donorid=donorid, token=token, dict_metadata=newdonor) == 'ok':
        flash(f'Updated metadata for {donorid}')
        return redirect('/')
