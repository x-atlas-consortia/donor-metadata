"""
Donor search form
"""
from flask import Blueprint, request, render_template, jsonify, abort, url_for, redirect
import requests

# The form used to execute a GET request against the entity-api of a consortium
from models.searchform import SearchForm

search_blueprint = Blueprint('search', __name__, url_prefix='/')


def getdonor(context: str, donorid: str, token: str) -> dict:
    """
    Searches for metadata for donor.
    :param context: consortium identifier used to build the URL for the entity-api endpoint.
    :param donorid: ID of a donor in the provenance database of a consortium.
    :param token: Globus group token, obtained from the app.cfg
    :return: if there is a donor entity with id=donorid, a dict that corresponds to the metadata
    object.
    """

    url = f'https://entity.api.{context}.org/entities/{donorid}'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    headers['Authorization'] = f'Bearer {token}'
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        rjson = response.json()
        if context=='hubmapconsortium':
            donor = rjson.get('hubmap_id')
        else:
            donor = rjson.get('sennet_id')
        return donor

    elif response.status_code == 404:
        abort(404, f'No donor with id {donorid} found in provenance for {context}')
    elif response.status_code == 400:
        err = response.json().get('error')
        if 'is not a valid id format' in err:
            # This is a miscoded error message. The error is 404, not 400.
            abort(404, f'No donor with id {donorid} found in provenance for {context}')
        else:
            abort(response.status_code, response.json().get('error'))
    else:
        abort(response.status_code, response.json().get('error'))


@search_blueprint.route('', methods=['GET', 'POST'])
def search():

    form = SearchForm(request.form)

    if request.method == 'POST' and form.validate():
        # Translate fields into the encoded donor metadata schema.

        context = dict(form.context.choices).get(form.context.data)
        donorid = form.donorid.data
        donorid = getdonor(context=context, donorid=donorid, token=form.token)
        return redirect(f'/edit/{donorid}')

    return render_template('index.html', form=form)
