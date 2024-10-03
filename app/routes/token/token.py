from flask import Blueprint, render_template, redirect, session

token_blueprint = Blueprint('token', __name__, url_prefix='/token')


@token_blueprint.route('', methods=['GET'])
def token():

    # Renders token help page.

    return render_template('token.html')

@token_blueprint.route('clear', methods=['GET'])
def token_clear():

    # Clears the session token

    if 'HMSNDonortoken' in session:
        session.pop('HMSNDonortoken', None)

    return redirect('/')