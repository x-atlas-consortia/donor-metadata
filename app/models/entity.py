# Class representing interactions with the entity-api for a donor.

from flask import abort
import requests
import json

# Represents the app.cfg file
from .appconfig import AppConfig

class Entity():

    def __init__(self, donorid: str):

        self.donorid = donorid
        self.consortium = self.__getconsortiumfromdonorid()

        # Build elements of endpoint url and header.
        self.cfg = AppConfig()
        self.urlbase = self.cfg.getfield(key='ENDPOINT_BASE').replace("'", "")
        self.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.token = self.cfg.getfield(key='GLOBUS_TOKEN').replace("'", "")
        self.headers['Authorization'] = f'Bearer {self.token}'


    def __getconsortiumfromdonorid(self) -> str:
        """
        Translates a consortium from a donor ID.

        :return: consortium identifier
        """

        contextid = self.donorid[0:3]
        if contextid == "HBM":
            consortium = 'hubmapconsortium'
        elif contextid == "SNT":
            consortium = 'sennetconsortium'
        else:
            msg = (f'Invalid donor id format: {self.donorid}. The first three characters of the id should be either '
               f'"HBM (for HuBMAP) or SNT (for SenNet).')
            abort(400, msg)

        return consortium


    def getdonormetadata(self) -> dict:
        """
        Searches for metadata for donor in a consortium, using the entity-api.
        :return: if there is a donor entity with id=donorid, a dict that corresponds to the metadata
        object.
        """

        url = f'{self.urlbase}.{self.consortium}.org/entities/{self.donorid}'
        response = requests.get(url=url, headers=self.headers)

        if response.status_code == 200:
            rjson = response.json()
            donor = rjson.get('metadata')
            return donor

        elif response.status_code == 404:
            abort(404, f'No donor with id {self.donorid} found in provenance for {self.consortium}')
        elif response.status_code == 400:
            err = response.json().get('error')
            if 'is not a valid id format' in err:
                # Translate this as a 404, not a 400.
                abort(404, f'No donor with id {self.donorid} found in provenance for {self.consortium}')
            else:
                abort(response.status_code, response.json().get('error'))
        else:
            abort(response.status_code, response.json().get('error'))

    def updatedonormetadata(self, dict_metadata: dict):
        """
        Updates  metadata for donor in a consortium, using the entity-api.
        :param dict_metadata: a dictionary of metadata per the entity schema.
        :return: nothing or aborts
        """

        url = f'{self.urlbase}.{self.consortium}.org/entities/{self.donorid}'
        data = {'metadata':dict_metadata}

        response = requests.put(url, json=data, headers=self.headers)

        if response.status_code not in [200, 201]:
            abort(response.status_code, response.json().get('error'))

        return 'ok'

    def has_published_datasets(self) -> bool:
        """
        Checks whether a donor is associated with published datasets in provenance.
        :return: boolean
        """
        url = f'{self.urlbase}.{self.consortium}.org/descendants/{self.donorid}'
        response = requests.get(url=url, headers=self.headers)

        if response.status_code == 200:
            rjson = response.json()

            haspublisheddatasets = False
            for e in rjson:
                entity_type = e.get('entity_type')
                if entity_type == 'Dataset':
                    status = e.get('status').lower()
                    if status == 'published':
                        haspublisheddatasets == True
                        break

            return haspublisheddatasets

        elif response.status_code == 404:
            abort(404, f'No donor with id {self.donorid} found in provenance for {self.consortium}')
        elif response.status_code == 400:
            err = response.json().get('error')
            if 'is not a valid id format' in err:
                # This is a miscoded error message. The error is 404, not 400.
                abort(404, f'No donor with id {self.donorid} found in provenance for {self.consortium}')
            else:
                abort(response.status_code, response.json().get('error'))
        else:
            abort(response.status_code, response.json().get('error'))
