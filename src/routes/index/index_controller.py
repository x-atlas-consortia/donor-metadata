# Home page controller

import os
from flask import Blueprint, jsonify, current_app, make_response, request, render_template

index_blueprint = Blueprint('index', __name__, url_prefix='/')

@index_blueprint.route('/', methods=['GET'])
def index_get():

    # Connect to the provenance neo4j instance.
    neo4j_instance = current_app.neo4jConnectionHelper.instance()

    # Load the home page that includes the data entry form.
    pageheader = f'{neo4j_instance.appcontext} Human Donor Clinical Metadata Registration'
    return render_template('index.html', pageheader=pageheader)