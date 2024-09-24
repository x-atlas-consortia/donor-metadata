"""
Represents clinical metadata associated with a donor in a consortium provenance database.
Uses a consortium's entity-api instance to:
1. get donor metadata
2. update donor metdata

"""

import requests
from flask import abort, request
import json

from models.entity import getdonormetadata, is_donor_for_published_datasets

class DonorData:

    def __init__(self, donorid: str, consortium: str, token: str, isforupdate: bool=False):
        """

        :param donorid: ID of a donor in a context.
        :param consortium: hubmapconsortium or sennetconsortium
        :param isforupdate: Is this for update?
        """

        self.donorid = donorid
        self.consortium = consortium
        self.token = token

        # The highest level key of the metadata dictionary is one of the following:
        # organ_donor_data
        # living_donor_data

        if isforupdate:
            self.metadata = {}
        else:
            self.metadata = getdonormetadata(donorid=donorid, consortium=consortium, token=token)
            if self.metadata is not None:
                metadata = self.metadata.get('organ_donor_data')
                if metadata is not None:
                    self.metadata_type = 'organ_donor_data'
                else:
                    metadata = self.metadata.get('living_donor_data')
                    if metadata is not None:
                        self.metadata_type = 'living_donor_data'
                    else:
                        msg = ("Invalid donor metadata. The highest-level key should be either "
                           "'organ_donor_data' or 'living_donor_data'.")
                        abort(400, msg)

            self.has_published_datasets = is_donor_for_published_datasets(donorid=donorid,
                                                                          consortium=consortium,
                                                                          token=token)

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

        if self.metadata is None:
            metadata = {}
        else:
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
            abort(500, "Invalid call to DonorData.getmetadatavalues: "
                       "both grouping_concept and list_concept are null")

        return listret

