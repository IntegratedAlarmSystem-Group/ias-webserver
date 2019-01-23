from alarms.interfaces import IAlarms


class ValueConnector:
    """
    This class defines methods to communicate the configurations
    for the displays with data from the alarm collection
    """

    @classmethod
    def get_antennas_to_pad_values(self):
        """
        Return a dictionary with the antennas to pad associations
        from the related IASValue in the values_collection
        """

        ANTENNAS_TO_PADS_VALUE_ID = "Array-AntennasToPads"

        selected_ias_value = IAlarms.get_value(ANTENNAS_TO_PADS_VALUE_ID)

        antennas_pads_association = selected_ias_value.value
        values = {}
        for item in antennas_pads_association.split(','):
            antenna_id, pad_placemark_id = item.split(':')
            values[antenna_id] = pad_placemark_id

        return values
