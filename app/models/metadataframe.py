# Class representing a set of metadata for a single donor, optimized for DataFrame opertaions such as
# export
import pandas as pd

class MetadataFrame:

    def __init__(self, metadata:list, donorid: str):
        """
        :param metadata: the metadata object for a donor entity.
        :param donorid: the id of a donor entity
        """

        self.dfexport = pd.DataFrame()
        listrows = []

        if metadata is not None:
            for m in metadata:
                # Flatten each metadata element for a donor into a row that includes the donor id and
                # source name. Order columns.
                mnew = {'id': donorid}
                for key in m:
                    print(key)
                    mnew[key] = m[key]

                # Create the metadata element into a DataFrame, wrapping the dict in a list.
                dfdonor = pd.DataFrame([mnew])
                listrows.append(dfdonor)

            # Concatenate flattened rows into dataframe for the donor.
            self.dfexport = pd.concat(listrows, ignore_index=True).fillna('')
