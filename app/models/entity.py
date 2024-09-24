# Functions related to executing endpoints in the entity-api.

from flask import abort
import requests
import json


def getconsortiumfromdonorid(donorid: str) -> str:
    """
    Tranlates the donorid into a consortium
    :param donorid: ID for a donor
    :return: consortium identifier
    """

    contextid = donorid[0:3]
    if contextid == "HBM":
        consortium = 'hubmapconsortium'
    elif contextid == "SNT":
        consortium = 'sennetconsortium'
    else:
        msg = (f'Invalid donor id format: {donorid}. The first three characters of the id should be either '
               f'"HBM (for HuBMAP) or SNT (for SenNet).')
        abort(400, msg)

    return consortium


def getdonormetadata(consortium: str, donorid: str, token: str) -> dict:
    """
    Searches for metadata for donor in a consortium, using the entity-api.
    :param consortium: consortium identifier used to build the URL for the entity-api endpoint.
    :param donorid: ID of a donor in the provenance database of a consortium.
    :param token: Globus group token, obtained from the app.cfg
    :return: if there is a donor entity with id=donorid, a dict that corresponds to the metadata
    object.
    """

    url = f'https://entity.api.{consortium}.org/entities/{donorid}'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    headers['Authorization'] = f'Bearer {token}'
    response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        rjson = response.json()
        donor = rjson.get('metadata')
        return donor

    elif response.status_code == 404:
        abort(404, f'No donor with id {donorid} found in provenance for {consortium}')
    elif response.status_code == 400:
        err = response.json().get('error')
        if 'is not a valid id format' in err:
            # This is a miscoded error message. The error is 404, not 400.
            abort(404, f'No donor with id {donorid} found in provenance for {consortium}')
        else:
            abort(response.status_code, response.json().get('error'))
    else:
        abort(response.status_code, response.json().get('error'))

def updatedonormetadata(consortium: str, donorid: str, token: str, dict_metadata: dict):
    """
    Updates  metadata for donor in a consortium, using the entity-api.
    :param consortium: consortium identifier used to build the URL for the entity-api endpoint.
    :param donorid: ID of a donor in the provenance database of a consortium.
    :param token: Globus group token, obtained from the app.cfg
    :param dict_metadata: a dictionary of metadata per the entity schema.
    :return: nothing or aborts
    """
    url = f'https://entity.api.{consortium}.org/entities/{donorid}'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(dict_metadata)

    # DEBUG
    print(f'url = {url}')
    print(f'data = {data}')
    print(f'headers = {headers}')

    #response = requests.put(url, json=data, headers=headers)

    #if response.status_code not in [200, 201]:
        #abort(response.status_code, response.json().get('error'))

    return 'ok'

def is_donor_for_published_datasets(consortium: str, donorid: str, token: str) -> bool:
    """
    Checkes whether a donor is associated with published datasets in provenance.
    :param consortium: consortium identifier used to build the URL for the entity-api endpoint.
    :param donorid: ID of a donor in the provenance database of a consortium.
    :param token: Globus group token, obtained from the app.cfg
    :return: boolean
    """
    url = f'https://entity.api.{consortium}.org/descendants/{donorid}'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        rjson = response.json()

        haspublisheddatasets = False
        for e in rjson:
            entity_type = e.get('entity_type')
            if entity_type == 'Dataset':
                status = e.get('status')
                haspublisheddatasets = haspublisheddatasets or status
        return haspublisheddatasets

    elif response.status_code == 404:
        abort(404, f'No donor with id {donorid} found in provenance for {consortium}')
    elif response.status_code == 400:
        err = response.json().get('error')
        if 'is not a valid id format' in err:
            # This is a miscoded error message. The error is 404, not 400.
            abort(404, f'No donor with id {donorid} found in provenance for {consortium}')
        else:
            abort(response.status_code, response.json().get('error'))
    else:
        abort(response.status_code, response.json().get('error'))
