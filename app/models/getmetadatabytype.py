# The metadata object of a donor entity has a first level key that can be one of the following:
# 1. living_donor_data
# 2. organ_donor_data
# The functions in this file handle the variable key.

from flask import abort

def getsource_name(dictmetadata:dict) -> str:
    """
    Returns the source name for a set of metadata.
    """
    listmetadata = dictmetadata.get('organ_donor_data')
    if listmetadata is not None:
        source_name = 'organ_donor_data'
    else:
        listmetadata = dictmetadata.get('living_donor_data')
        if listmetadata is None:
            msg = ("Invalid donor metadata. The highest-level key should be either "
                   "'organ_donor_data' or 'living_donor_data'.")
            abort(500, msg)

        source_name = 'living_donor_data'

    return source_name


def getmetadatabytype(dictmetadata:dict) -> list:
    """
    The key for a donor's metadata object can be either 'organ_donor_data' or 'living_donor_data.'

    :param dictmetadata: a donor metadata object.
    :return: a list of metadata elements (dicts).
    """
    source_name = getsource_name(dictmetadata)
    listmetadata = dictmetadata.get(source_name)

    # Add the source_name to the metadata elements.
    listmetadatawithsource = []
    for m in listmetadata:
        mnew = {'source_name': source_name}
        for key in m:
            mnew[key] = m[key]
        listmetadatawithsource.append(mnew)

    return listmetadatawithsource