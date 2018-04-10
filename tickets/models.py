from django.db import models
from django.utils import timezone
from utils.choice_enum import ChoiceEnum


class TicketStatus(ChoiceEnum):

    OPEN = 1
    CLOSE = 0

    @classmethod
    def options(cls):
        """ Return a list of tuples with the valid options. """
        return cls.get_choices()


class Ticket(models.Model):
    """ Ticket associated to an alarm that needs to be acknowledged """

    created_at = models.DateTimeField(auto_now_add=True)
    """ Time when the ticket is created """

    resolve_at = models.DateTimeField(null=True)
    """ Time when the ticket is updated """

    alarm_id = models.CharField(max_length=64)
    """ Reference to the related alarm """

    message = models.CharField(max_length=256, null=True)
    """ Message posted when the ticket is closed """

    status = models.IntegerField(
        choices=TicketStatus.options(),
        default=1,
    )
    """ State of the ticket, default is open """

    def resolve(self, message):
        """ Resolves the ticket modifying the status, the resolution timestamp
        and the message """
        if message.strip() is not "" and self.status == 1:
            self.status = 0
            self.resolve_at = timezone.now()
            self.message = message
            self.save()
            return "solved"
        return "ignored"
