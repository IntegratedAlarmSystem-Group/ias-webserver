import json
import os
from ias_webserver.settings import (
    CDB_LOCATION,
    TEST_CDB_LOCATION,
    IAS_FILE,
    IASIOS_FILE,
    DASUS_FOLDER,
    TEMPLATES_FILE,
    BROADCAST_RATE_FACTOR
)


class CdbReader:
    """ Defines a reader for the CDB """

    @classmethod
    def get_cdb_location(self):
        testing = os.environ.get('TESTING', False)
        if testing:
            return TEST_CDB_LOCATION
        else:
            return CDB_LOCATION

    @classmethod
    def read_ias(self):
        """
        Reads the ias.json file of the CDB and initializes what is necessary
        for the application to start

        Returns:
            dict: A dictionary with the IAS configuration data
        """
        filepath = self.get_cdb_location() + IAS_FILE
        with open(filepath) as file:
            ias_data = json.load(file)
        ias_data['broadcastFactor'] = str(BROADCAST_RATE_FACTOR)
        return ias_data

    @classmethod
    def read_alarm_iasios(self):
        """
        Reads the IASIOs form the CDB that will become alarms

        Returns:
            dict: A list of IASIOs data
        """
        iasios = self.read_iasios_file()
        templates = self.read_templates()
        valid_iasios = []
        dasu_outputs = self.read_dasus_outputs()
        if not dasu_outputs or dasu_outputs == []:
            return None
        for iasio in iasios:
            if iasio["id"] not in dasu_outputs or iasio["iasType"] != "ALARM":
                continue
            if "templateId" not in iasio:
                valid_iasios.append(iasio)
            else:
                template_range = CdbReader.find_template_range(
                    iasio['templateId'], templates
                )
                for i in template_range:
                    aux_iasio = iasio.copy()
                    aux_iasio['id'] = aux_iasio['id'] + ' instance ' + str(i)
                    valid_iasios.append(aux_iasio)

        return valid_iasios

    @classmethod
    def read_iasios_file(self):
        """
        Reads the ioasios.json file with all the IASIOs

        Returns:
            dict: A list of IASIOs data
        """
        filepath = self.get_cdb_location() + IASIOS_FILE
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
        folder = self.get_cdb_location() + DASUS_FOLDER
        filepaths = [
            folder + f for f in os.listdir(folder) if f.endswith('.json')
        ]
        iasios = []
        for filepath in filepaths:
            with open(filepath) as file:
                dasu = json.load(file)
            if "outputId" not in dasu:
                continue
            output = dasu["outputId"]
            iasios.append(output)
        return iasios

    @classmethod
    def read_templates(self):
        """
        Reads the templates.json file from the CDB and returns its content

        Returns:
            dict: A list of templates data
        """
        filepath = self.get_cdb_location() + TEMPLATES_FILE
        with open(filepath) as file:
            templates = json.load(file)
        return templates

    @classmethod
    def find_template_range(self, template_id, templates):
        """
        Returns the range of the temaplate

        Args:
            template_id (string): the themplate of the ID
            templates (list): list of dictionaries with the templates

        Returns:
            dict: A range with the numbers of the template
            (including max and min)
        """
        for template in templates:
            if template['id'] == template_id:
                return range(int(template['min']), int(template['max']) + 1)
        return None
