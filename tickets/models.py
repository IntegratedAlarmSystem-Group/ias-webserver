from django.db import models
from django.utils import timezone
from utils.choice_enum import ChoiceEnum


class TicketStatus(ChoiceEnum):

    ACK = 1
    UNACK = 0

    @classmethod
    def options(cls):
        """ Return a list of tuples with the valid options. """
        return cls.get_choices()


class Ticket(models.Model):
    """ Ticket associated to an alarm that needs to be acknowledged """

    created_at = models.DateTimeField(auto_now_add=True)
    """ Time when the ticket is created """

    acknowledged_at = models.DateTimeField(null=True)
    """ Time when the ticket is updated """

    alarm_id = models.CharField(max_length=64, db_index=True)
    """ Reference to the related alarm """

    message = models.CharField(max_length=256, null=True)
    """ Message posted when the ticket is closed """

    status = models.IntegerField(
        choices=TicketStatus.options(),
        default=int(TicketStatus.get_choices_by_name()['UNACK']),
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

    def acknowledge(self, message):
        """ Resolves the ticket modifying the status, the resolution timestamp
        and the message """
        if self.status == int(TicketStatus.get_choices_by_name()['ACK']):
            return "ignored-ticket-ack"
        if message.strip() is "":
            return "ignored-wrong-message"

        self.status = int(TicketStatus.get_choices_by_name()['ACK'])
        self.acknowledged_at = timezone.now()
        self.message = message
        self.save()
        return "solved"
