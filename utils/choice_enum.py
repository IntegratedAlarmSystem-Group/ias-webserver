import inspect
from enum import Enum


class ChoiceEnum(Enum):

    @classmethod
    def get_choices(cls):
        """Returns choices available"""
        # get class members:
        members = inspect.getmembers(cls, lambda m: not(inspect.isroutine(m)))
        # get only members which are properties:
        properties = [memb for memb in members if not(memb[0][:2] == '__')]
        # format to djano choice tuple:
        choices = tuple([(str(prop[1].value), prop[0]) for prop in properties])
        return choices
