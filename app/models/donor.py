"""
Represents clinical metadata associated with a donor in a consortium database.
"""

import requests
from flask import abort

class DonorData:

    def __getdonormetadata(self, consortium: str, donorid: str, token: str) -> dict:
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
            if consortium == 'hubmapconsortium':
                donor = rjson.get('metadata')
            else:
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

    def __init__(self, donorid: str, consortium: str, token: str):
        """

        :param donorid: ID of a donor in a context.
        :param consortium: hubmapconsortium or sennetconsortium
        """

        self.metadata = self.__getdonormetadata(donorid=donorid, consortium=consortium, token=token)
        self.donorid = donorid
        self.consortium = consortium
        self.token = token

        # The highest level key of the metadata dictionary is one of the following:
        # organ_donor_data
        # living_donor_data

        metadata = self.metadata.get('organ_donor_data')
        if metadata is not None:
            self.metadata_type = 'organ_donor_data'
        else:
            metadata = self.metadata.get('living_donor_data')
            if metadata is not None:
                self.metadata_type = 'living_donor_data'
            else:
                msg = ("Invalid donor metadata. The highest-level key should be "
                       "either 'organ_donor_data' or 'living_donor_data'.")
                abort(400, msg)

    def getmetadatavalues(self, key: str, grouping_concept=None, list_concept=None) -> list:
        """
        Returns donor metadata of a specified type.
        :param grouping_concept: Corresponds to the "grouping_concept" column of a tab in the
        donor metadata valueset
        :param concept_list: Optional list Corresponding to a group of related concepts.
        NOTE: grouping_concept takes precedence over concept_list.
        :param key: key in the dictionary of metadata
        :return: the value in the metadata dictionary corresponding to key
        """

        metadata = self.metadata.get(self.metadata_type)
        # Donor metadata is a list of dicts.

        # Extract the relevant metadata dicts from the list, and then the relevant value from each dict.
        listret = []

        if grouping_concept is not None:
            for m in metadata:
                group = m.get('grouping_concept')
                if group == grouping_concept:
                    val = m.get(key)
                    if val is not None:
                        listret.append(val)
        elif list_concept is not None:
            for m in metadata:
                m_concept = m.get('concept_id')
                m_term = m.get('data_value')
                if m_concept in list_concept:
                    val = m.get(key)
                    if val is not None:
                        listret.append(val)
        else:
            abort(500, "Invalid call to donordata.getmetadatavalues: "
                       "both grouping_concept and list_concept are null")


        return listret

