from datetime import timedelta
from django.db import models
from django.utils import timezone
from utils.choice_enum import ChoiceEnum


class TicketStatus(ChoiceEnum):
    """ Status options of a Ticket """

    ACK = 1
    """ Acknowledged """

    UNACK = 0
    """ Unacknowledged """

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

    def __str__(self):
        """ Return a string representation of the ticket """
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
        if self.status == int(TicketStatus.get_choices_by_name()['ACK']):
            return "ignored-ticket-ack"
        if message.strip() is "":
            return "ignored-wrong-message"

        self.status = int(TicketStatus.get_choices_by_name()['ACK'])
        self.acknowledged_at = timezone.now()
        self.message = message
        self.save()
        return "solved"


class ShelveRegistryStatus(ChoiceEnum):
    """ Status options of a ShelveRegistry """

    SHELVED = 1
    """ Shelved """

    UNSHELVED = 0
    """ Unshelved """

    @classmethod
    def options(cls):
        """ Return a list of tuples with the valid options. """
        return cls.get_choices()


class ShelveRegistry(models.Model):
    """ Registry of when an alarm is shelved """

    shelved_at = models.DateTimeField(auto_now_add=True)
    """ Time when the alarm is shelved """

    unshelved_at = models.DateTimeField(null=True)
    """ Time when the alarm is unshelved """

    alarm_id = models.CharField(max_length=64, db_index=True)
    """ Reference to the related alarm """

    message = models.CharField(max_length=256, null=False, blank=False)
    """ Message posted when the ticket is closed """

    timeout = models.DurationField(default=timedelta(hours=2))
    """ Timeout after which a shelved Alarm must be unshelved """

    status = models.IntegerField(
        choices=ShelveRegistryStatus.options(),
        default=int(ShelveRegistryStatus.get_choices_by_name()['SHELVED']),
    )
    """ State of the shelve_registry, default is shelved """

    def __str__(self):
        """ Return a string representation of the shelve_registry """
        return str(self.shelved_at) + ' - ' + self.alarm_id

    def save(self, *args, **kwargs):
        """ Check if the message is not empty before saving """
        if not self.message or self.message == '':
            raise ValueError("Registry message cannot be empty")
        super().save(*args, **kwargs)

    def to_dict(self):
        """ Return the shelve_registry as a dictionary """
        return {
            'shelved_at': str(self.shelved_at),
            'unshelved_at': str(self.unshelved_at),
            'alarm_id': self.alarm_id,
            'message': self.message,
            'status': self.status
        }

    def unshelve(self):
        """ Unshelves the registry modifying the status and the resolution
        timestamp """
        status = int(ShelveRegistryStatus.get_choices_by_name()['UNSHELVED'])
        if self.status == status:
            return "ignored-unshelved-ack"
        self.status = status
        self.unshelved_at = timezone.now()
        self.save()
        return "unshelved"
