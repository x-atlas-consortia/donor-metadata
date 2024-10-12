"""
Login route
Logs into a consortium's Globus environment.

"""

from flask import Blueprint, request, render_template, redirect, session, abort, url_for
from globus_sdk import AccessTokenAuthorizer, AuthClient, ConfidentialAppAuthClient
import json

# Helper classes
from models.appconfig import AppConfig

login_blueprint = Blueprint('login', __name__, url_prefix='/login')


def get_user_info(token):
    auth_client = AuthClient(authorizer=AccessTokenAuthorizer(token))
    return auth_client.oauth2_userinfo()


def load_app_client(consortium: str) -> ConfidentialAppAuthClient:

    """
    Initiates a Globus aopp client, based on the consortium.
    :param consortium: identifies a Globus environment
    """
    cfg = AppConfig()

    if consortium == 'CONTEXT_HUBMAP':
        globus_client = cfg.getfield(key='GLOBUS_HUBMAP_CLIENT')
        globus_secret = cfg.getfield(key='GLOBUS_HUBMAP_SECRET')
    elif consortium == 'CONTEXT_SENNET':
        globus_client = cfg.getfield(key='GLOBUS_HUBMAP_CLIENT')
        globus_secret = cfg.getfield(key='GLOBUS_HUBMAP_SECRET')
    else:
        msg = f'Unknown consortium: {consortium}. Check the configuration file.'
        abort(msg, 400)

    return ConfidentialAppAuthClient(globus_client, globus_secret)


@login_blueprint.route('', methods=['POST', 'GET'])
def login():
    """
    Login via Globus Auth.
    May be invoked in one of two scenarios:
    1. Login is starting, no state in Globus Auth yet
    2. Returning to application during login, already have short-lived code from Globus Auth to exchange
       for tokens, encoded in a query param
    """
    # Set Globus environment based on the selected consortium.
    consortium = session['consortium']
    client = load_app_client(consortium)

    redirect_uri = 'http://127.0.0.1:5002/login'
    #redirect_uri = 'https://portal.hubmapconsortium.org/login'
    client.oauth2_start_flow(redirect_uri, refresh_tokens=True)

    # If there's no "code" query string parameter, we're in this route
    # starting a Globus Auth login flow.
    # Redirect out to Globus Auth
    if 'code' not in request.args:
        params: dict = {"scope": "openid profile email"
                                 " urn:globus:auth:scope:transfer.api.globus.org:all"
                                 " urn:globus:auth:scope:auth.globus.org:view_identities"
                                 " urn:globus:auth:scope:nexus.api.globus.org:groups"
                                 " urn:globus:auth:scope:groups.api.globus.org:all"}
        auth_uri = client.oauth2_get_authorize_url(query_params=params)
        return redirect(auth_uri)

    # If we do have a "code" param, we're coming back from Globus Auth
    # and can start the process of exchanging an auth code for a token.
    else:
        auth_code = request.args.get('code')

        token_response = client.oauth2_exchange_code_for_tokens(auth_code)

        # Get all Bearer tokens
        auth_token = token_response.by_resource_server['auth.globus.org']['access_token']
        # nexus_token = token_response.by_resource_server['nexus.api.globus.org']['access_token']
        transfer_token = token_response.by_resource_server['transfer.api.globus.org']['access_token']
        groups_token = token_response.by_resource_server['groups.api.globus.org']['access_token']
        # Also get the user info (sub, email, name, preferred_username) using the AuthClient with the auth token
        user_info = get_user_info(auth_token)

        info = {
            'name': user_info['name'],
            'email': user_info['email'],
            'globus_id': user_info['sub'],
            'auth_token': auth_token,
            # 'nexus_token': nexus_token,
            'transfer_token': transfer_token,
            'groups_token': groups_token
        }

        # Store the resulting tokens in server session
        session.update(
            tokens=token_response.by_resource_server
        )

        # Finally redirect back to the client
        json_str: str = json.dumps(info)
        return redirect(f'/search?info={str(json_str)}')



