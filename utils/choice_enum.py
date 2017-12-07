import inspect
from enum import Enum


class ChoiceEnum(Enum):

    @classmethod
    def get_choices(cls):
        """Returns the available choices as a list of tuples"""
        # get class members:
        members = inspect.getmembers(cls, lambda m: not(inspect.isroutine(m)))
        # get only members which are properties:
        properties = [memb for memb in members if not(memb[0][:2] == '__')]
        # format to djano choice tuple:
        choices = tuple([(str(prop[1].value), prop[0]) for prop in properties])
        return choices

    @classmethod
    def get_choices_by_value(cls):
        """Returns the available choices as a dict indexed by value"""
        choices = cls.get_choices()
        return dict(choices)

    @classmethod
    def get_choices_by_name(cls):
        """Returns the available choices as a dict indexed by name"""
        choices = dict((y, x) for x, y in cls.get_choices())
        return dict(choices)
