from flask import Blueprint, render_template

token_blueprint = Blueprint('token', __name__, url_prefix='/token')


@token_blueprint.route('', methods=['GET'])
def token():

    # Renders token help page.

    return render_template('token.html')
