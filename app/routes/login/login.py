# Home page controller

import os
from flask import Blueprint, jsonify, current_app, make_response, request, render_template

login_blueprint = Blueprint('login', __name__, url_prefix='/')

@login_blueprint.route('/', methods=['GET'])
def login_get():

    # Connect to the provenance neo4j instance.
    #neo4j_instance = current_app.neo4jConnectionHelper.instance()

    # Load the home page that includes the data entry form.
    return render_template('login.html')