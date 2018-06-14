from django.db import models
from django.utils import timezone
from utils.choice_enum import ChoiceEnum


class TicketStatus(ChoiceEnum):

    UNACK = 0
    ACK = 1
    CLEARED_UNACK = 2
    CLEARED_ACK = 3

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

    cleared_at = models.DateTimeField(null=True)
    """ Time when the associated alarm is cleared """

    alarm_id = models.CharField(max_length=64, db_index=True)
    """ Reference to the related alarm """

    message = models.CharField(max_length=256, null=True)
    """ Message posted when the ticket is closed """

    status = models.IntegerField(
        choices=TicketStatus.options(),
        default=int(TicketStatus.get_choices_by_name()['UNACK']),
    )
    """ State of the ticket, default is open """

    def __str__(self):
        """ Return a string representation of a ticket """
        return str(self.created_at) + ' - ' + self.alarm_id

    def to_dict(self):
        """ Return the ticket as a dictionary """
        return {
            'created_at': self.created_at,
            'acknowledged_at': self.acknowledged_at,
            'alarm_id': self.alarm_id,
            'message': self.message,
            'status': self.status
        }

    def acknowledge(self, message):
        """ Resolves the ticket modifying the status, the resolution timestamp
        and the message """
        ack = TicketStatus.get_choices_by_name()['ACK']
        unack = TicketStatus.get_choices_by_name()['UNACK']
        cleared_ack = TicketStatus.get_choices_by_name()['CLEARED_ACK']
        cleared_unack = TicketStatus.get_choices_by_name()['CLEARED_UNACK']

        if self.status == int(ack) or self.status == int(cleared_ack):
            return "ignored-ticket-ack"
        if message.strip() is "":
            return "ignored-wrong-message"

        if self.status == int(unack):
            self.status = int(ack)
        elif self.status == int(cleared_unack):
            self.status = int(cleared_ack)
        self.acknowledged_at = timezone.now()
        self.message = message
        self.save()
        return "solved"

    def clear(self):
        """ Records the time when the associated alarm was cleared and update
        the ticket state """
        ack = TicketStatus.get_choices_by_name()['ACK']
        unack = TicketStatus.get_choices_by_name()['UNACK']
        cleared_ack = TicketStatus.get_choices_by_name()['CLEARED_ACK']
        cleared_unack = TicketStatus.get_choices_by_name()['CLEARED_UNACK']

        self.cleared_at = timezone.now()
        if self.status == int(ack):
            self.status = int(cleared_ack)
        elif self.status == int(unack):
            self.status = int(cleared_unack)
        self.save()
