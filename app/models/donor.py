"""
Represents clinical metadata associated with a donor in a consortium provenance database.
Uses a consortium's entity-api instance to:
1. get donor metadata
2. update donor metdata

"""

from flask import abort

# Helper classes
# Entity-api functions
from models.entity import Entity
# April 2025
# To obtain DOI information
from models.searchapi import SearchAPI

class DonorData:

    def __init__(self, donorid: str, token: str, isforupdate: bool = False):
        """
        :param donorid: ID of a donor in a context.
        :param isforupdate: Is this for an update, or existing metadata?
        :param token: globus groups_token for the consortium's entity-api
        """

        self.donorid = donorid
        self.entity = Entity(donorid=donorid, token=token)
        self.consortium = self.entity.consortium

        # The highest level key of the metadata dictionary is one of the following:
        # organ_donor_data
        # living_donor_data

        if isforupdate:
            # This instance will contain new metadata.
            self.metadata = {}
        else:
            # This instance will contain existing metadata.
            self.metadata = self.entity.getdonormetadata()

    def getmetadatavalues(self, key: str, grouping_concept=None, list_concept=None) -> list:
        """
        Returns donor metadata of a specified type.
        :param grouping_concept: Corresponds to the "grouping_concept" column of a tab in the
        donor metadata valueset
        :param list_concept: Optional list Corresponding to a group of related concepts,
                             **filtered by** grouping_concept.
        :param key: key in the dictionary of metadata
        :return: the value in the metadata dictionary corresponding to key
        """

        if self.metadata is None:
            return []

        # If the donor has metadata, the metadata object is a dict in form:
        # {<key>:[list of dicts]}
        # in which <key> is either 'living_donor_data' or 'organ_donor_data'.
        # Get the list of metadata elements.
        source_name = 'living_donor_data'
        if source_name not in self.metadata.keys():
            source_name = 'organ_donor_data'
        if source_name not in self.metadata.keys():
            abort(500,'unknown donor metadata key')

        listmetadata = self.metadata.get(source_name)

        # Extract the relevant metadata dicts from the list, and then the relevant value from each dict.
        listret = []

        if list_concept is not None:
            for m in listmetadata:
                m_concept = m.get('concept_id').strip()
                if m_concept in list_concept:
                    group = m.get('grouping_concept').strip()
                    if group == grouping_concept:
                        val = m.get(key)
                        if val is not None:
                            listret.append(val)
        elif grouping_concept is not None:
            for m in listmetadata:
                group = m.get('grouping_concept').strip()
                if group == grouping_concept:
                    val = m.get(key)
                    if val is not None:
                        listret.append(val)
        else:
            abort(400, "Invalid call to DonorData.getmetadatavalues: "
                       "both grouping_concept and list_concept are null")

        return listret

    def updatedonormetadata(self, dict_metadata: dict):
        """
        Pass-through to the Entity object's call.
        :param dict_metadata: a dictionary of metadata per the entity schema.
        :return: ok or abort
        """
        return self.entity.updatedonormetadata(dict_metadata=dict_metadata)
