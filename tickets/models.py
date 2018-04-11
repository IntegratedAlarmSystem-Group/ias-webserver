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

    resolved_at = models.DateTimeField(null=True)
    """ Time when the ticket is updated """

    alarm_id = models.CharField(max_length=64, db_index=True)
    """ Reference to the related alarm """

    message = models.CharField(max_length=256, null=True)
    """ Message posted when the ticket is closed """

    status = models.IntegerField(
        choices=TicketStatus.options(),
        default=1,
    )
    """ State of the ticket, default is open """

    def to_dict(self):
        """ Return the ticket as a dictionary """
        return {
            'created_at': self.created_at,
            'resolved_at': self.resolved_at,
            'alarm_id': self.alarm_id,
            'message': self.message,
            'status': self.status
        }

    def resolve(self, message):
        """ Resolves the ticket modifying the status, the resolution timestamp
        and the message """
        if self.status == 0:
            return "ignored-ticket-closed"
        if message.strip() is "":
            return "ignored-wrong-message"

        self.status = 0
        self.resolved_at = timezone.now()
        self.message = message
        self.save()
        return "solved"
