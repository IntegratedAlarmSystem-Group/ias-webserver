from alarms.interfaces import IAlarms


class ValueConnector:
    """
    This class defines methods to communicate the configurations
    for the displays with data from the alarm collection
    """

    @classmethod
    def get_value(self, value_id):
        """
        Get a selected IASValue from the values_collection

        Args:
        value_id (string): The core_id of the value
        """
        return IAlarms.get_value(value_id)
