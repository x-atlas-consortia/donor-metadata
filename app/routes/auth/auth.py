"""
Globus auth routes.

"""

from flask import Blueprint, request, redirect, session, abort
from globus_sdk import AccessTokenAuthorizer, AuthClient, ConfidentialAppAuthClient


# Helper classes
from models.appconfig import AppConfig


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
        globus_client = cfg.getfield(key='GLOBUS_SENNET_CLIENT')
        globus_secret = cfg.getfield(key='GLOBUS_SENNET_SECRET')
    else:
        msg = f'Unknown consortium: {consortium}. Check the configuration file.'
        abort(400, msg)

    return ConfidentialAppAuthClient(globus_client, globus_secret)


login_blueprint = Blueprint('login', __name__, url_prefix='/login')

@login_blueprint.route('', methods=['GET'])
def login():
    """
    Login via Globus Auth for the curation and export workflows.

    This route is invoked twice for a workflow.

    1. Before authentication to Globus,
       a. The Globus Auth session has no value for the "state" argument of the request.
       b. The Globus environment (consortium) and donor id are stored as session variables.
       c. After establishing the appropriate client, the route executes oauth2_start_flow, which redirects
          first to Globus oauth and then back to itself
    2. After authentication in Globus,
       a. The Globus Auth session has a value for the "code" argument of the request that can be
          exchanged for tokens.
       b. The Globus environment (consortium) and donorid are returned in the "state" argument of the
          request.

    """

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    # Obtain consortium and donorid.
    if 'state' in request.args:
        consortium = request.args.get('state').split(' ')[0]
        donorid = request.args.get('state').split(' ')[1]
    else:
        consortium = session['consortium']
        donorid = session['donorid']

    client = load_app_client(consortium)

    # The Globus Auth session will redirect to this route.
    redirect_uri = f'http://localhost:5000/login'
    client.oauth2_start_flow(redirect_uri, refresh_tokens=True)

    # If there's no "code" argument in the request object, then this is the first execution of the route.
    # Redirect out to Globus Auth, identifying the consortium and donor id via the state key.
    if 'code' not in request.args:
        state = f'{session["consortium"]} {session["donorid"]}'
        params: dict = {"scope": "openid profile email"
                                 " urn:globus:auth:scope:transfer.api.globus.org:all"
                                 " urn:globus:auth:scope:auth.globus.org:view_identities"
                                 " urn:globus:auth:scope:groups.api.globus.org:all",
                        "state": state}
        auth_uri = client.oauth2_get_authorize_url(query_params=params)
        return redirect(auth_uri)

    # If the request contains a code argument, then this is the second execution of the route, returning from
    # Globus Auth. Exchange the auth code for a token.
    else:
        auth_code = request.args.get('code')
        token_response = client.oauth2_exchange_code_for_tokens(auth_code)

        # Get all Bearer tokens
        auth_token = token_response.by_resource_server['auth.globus.org']['access_token']
        print(auth_token)
        # nexus_token = token_response.by_resource_server['nexus.api.globus.org']['access_token']
        # transfer_token = token_response.by_resource_server['transfer.api.globus.org']['access_token']
        groups_token = token_response.by_resource_server['groups.api.globus.org']['access_token']
        # Also get the user info (sub, email, name, preferred_username) using the AuthClient with the auth token
        user_info = get_user_info(auth_token)

        session['groups_token'] = groups_token
        session['consortium'] = consortium
        session['donorid'] = donorid
        session['userid'] = user_info.get('preferred_username')

        # Redirect to the appropriate page, based  on the workflow.
        if donorid == 'ALL':
            return redirect(f'/export/review')
        else:
            return redirect(f'/edit')
