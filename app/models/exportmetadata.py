# Class representing donor metadata optimized for export.
import pandas as pd

# Helper class
from .donor import DonorData


class ExportMetadata:

    def __init__(self, donor: DonorData, consortium: str):
        """

        :param donor: A Donor object
        :param consortium: globus consortium identifier
        """

        self.dfexport = pd.DataFrame()
        listrows = []

        # Only return metadata for human sources in SenNet.
        if consortium == 'sennetconsortium.org':
            entity_type = donor.source_type
            getdonor = entity_type == 'Human'
        else:
            getdonor = True

        if getdonor:
            donor_metadata = donor.get('metadata')
            # Metadata is keyed differently based on whether the donor was living or an organ donor.
            if donor_metadata is not None:
                if 'organ_donor_data' in donor_metadata.keys():
                    source_name = 'organ_donor_data'
                else:
                    source_name = 'living_donor_data'

                # ID key is based on consortium.
                if consortium == 'hubmapconsortium.org':
                    donorid = donor['hubmap_id']
                else:
                    donorid = donor['sennet_id']

                metadata = donor_metadata.get(source_name)
                if metadata is not None:
                    for m in metadata:
                        # Flatten each metadata element for a donor into a row that includes the donor id and
                        # source name. Order columns.
                        mnew = {}
                        mnew['id'] = donorid
                        mnew['source_name'] = source_name
                        for key in m:
                            mnew[key] = m[key]

                        # Create the metadata element into a DataFrame, wrapping the dict in a list.
                        dfdonor = pd.DataFrame([mnew])
                        listrows.append(dfdonor)

                    # Concatenate flattened rows into dataframe for the donor.
                    self.dfexport = pd.concat(listrows, ignore_index=True)