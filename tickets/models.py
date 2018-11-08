import logging
from datetime import timedelta
from django.db import models
from django.utils import timezone
from utils.choice_enum import ChoiceEnum

logger = logging.getLogger(__name__)


PERMISSIONS = ('add', 'change', 'delete', 'view')
""" Models Permissions """

ACK_TICKET_PERMISSIONS = PERMISSIONS + ('acknowledge',)
""" Ack ticket permissions """

SHELVE_REGISTRY_PERMISSIONS = PERMISSIONS + ('shelve',)
""" Shelve registry permissions """


class TicketStatus(ChoiceEnum):
    """ Status options of a Ticket """

    UNACK = 0
    """ Uncknowledged """

    ACK = 1
    """ Acknowledged """

    CLEARED_UNACK = 2
    """ Cleared and Unacknowledged """

    CLEARED_ACK = 3
    """ Cleared and Acknowledged """

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

    class Meta:
        default_permissions = ACK_TICKET_PERMISSIONS
    """ Additional options for the model """

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
        ack = TicketStatus.get_choices_by_name()['ACK']
        unack = TicketStatus.get_choices_by_name()['UNACK']
        cleared_ack = TicketStatus.get_choices_by_name()['CLEARED_ACK']
        cleared_unack = TicketStatus.get_choices_by_name()['CLEARED_UNACK']

        if self.status == int(ack) or self.status == int(cleared_ack):
            logger.debug(
                'fail acknowledge because the ticket %d was already ack',
                self.id)
            return "ignored-ticket-ack"
        if message.strip() is "":
            logger.debug(
                'fail acknowledge of ticket %d because the message is empty',
                self.id)
            return "ignored-wrong-message"

        if self.status == int(unack):
            self.status = int(ack)
        elif self.status == int(cleared_unack):
            self.status = int(cleared_ack)
        self.acknowledged_at = timezone.now()
        self.message = message
        self.save()
        logger.debug("the ticket %d was acknowledged", self.id)
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
        logger.debug("the ticket %d was cleared", self.id)
        self.save()

    @staticmethod
    def has_read_permission(request):
        return request.user.has_perm('tickets.view_ticket')

    def has_object_read_permission(self, request):
        return request.user.has_perm('tickets.view_ticket')

    @staticmethod
    def has_acknowledge_permission(request):
        return request.user.has_perm('tickets.acknowledge_ticket')


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

    timeout = models.DurationField(default=timedelta(hours=12))
    """ Timeout after which a shelved Alarm must be unshelved """

    status = models.IntegerField(
        choices=ShelveRegistryStatus.options(),
        default=int(ShelveRegistryStatus.get_choices_by_name()['SHELVED']),
    )
    """ State of the shelve_registry, default is shelved """

    class Meta:
        default_permissions = SHELVE_REGISTRY_PERMISSIONS
    """ Additional options for the model """

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
            logger.debug(
                'failed unshelve, the registry %d was already unshelved',
                self.id)
            return "ignored-unshelved-ack"
        self.status = status
        self.unshelved_at = timezone.now()
        self.save()
        logger.debug('the registry %d was unshelved', self.id)
        return "unshelved"

    @staticmethod
    def has_create_permission(request):
        return request.user.has_perm('tickets.add_shelveregistry')

    @staticmethod
    def has_read_permission(request):
        return request.user.has_perm('tickets.view_shelveregistry')

    def has_object_read_permission(self, request):
        return request.user.has_perm('tickets.view_shelveregistry')

    @staticmethod
    def has_update_permission(request):
        return request.user.has_perm('tickets.change_shelveregistry')

    def has_object_update_permission(self, request):
        return request.user.has_perm('tickets.change_shelveregistry')

    @staticmethod
    def has_destroy_permission(request):
        return request.user.has_perm('tickets.delete_shelveregistry')

    def has_object_destroy_permission(self, request):
        return request.user.has_perm('tickets.delete_shelveregistry')

    @staticmethod
    def has_check_timeouts_permission(request):
        return True
