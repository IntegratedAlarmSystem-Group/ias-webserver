import json
import os
from ias_webserver.settings import (
    CDB_LOCATION,
    IAS_FILE,
    IASIOS_FILE,
    DASUS_FOLDER
)


class IasReader:
    """ Class that defines a reader for the ias.json file of the CDB """

    @classmethod
    def read_ias(self):
        """
        Reads the IAS json file of the CDB and initializes what is necessary
        for the application to start

        Returns:
            dict: A dictionary with the IAS configuration data
        """
        filepath = CDB_LOCATION +  IAS_FILE
        with open(filepath) as file:
            ias_data = json.load(file)
        return ias_data


class IasiosReader:
    """ Class that defines a reader for the IASIOs from the CDB """

    @classmethod
    def read_alarm_iasios(self):
        """
        Reads the IASIOs form the CDB that will become alarms

        Returns:
            dict: A dictionary of IASIOs data
        """
        iasios = self.read_iasios_file()
        valid_iasios = []
        dasu_outputs = self.read_dasus_outputs()
        if not dasu_outputs or dasu_outputs == []:
            return None
        for iasio in iasios:
            if "id" in iasio and iasio["id"] in dasu_outputs:
                valid_iasios.append(iasio)
        return valid_iasios

    @classmethod
    def read_iasios_file(self):
        """
        Reads the ioasios.json file with all the IASIOs

        Returns:
            dict: A dictionary of IASIOs data
        """
        filepath = CDB_LOCATION +  IASIOS_FILE
        with open(filepath) as file:
            iasios = json.load(file)
        return iasios

    @classmethod
    def read_dasus_outputs(self):
        """
        Reads the DASU json files and returns a list with all their outputs

        Returns:
            dict: A list IASIOs ids
        """
        folder = CDB_LOCATION +  DASUS_FOLDER
        filepaths = [
            folder + f for f in os.listdir(folder) if f.endswith('.json')
        ]
        iasios = []
        for filepath in filepaths:
            with open(filepath) as file:
                dasu = json.load(file)
                if "outputId" in dasu:
                    output = dasu["outputId"]
                    iasios.append(output)
        return iasios
