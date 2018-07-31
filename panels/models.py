from django.db import models


class File(models.Model):
    """ General purpose file """

    key = models.CharField(max_length=30, unique=True)
    """ Key to identify the File on the client side """

    url = models.CharField(max_length=256)
    """ URL with the location of the File """

    def __str__(self):
        """ Return a string representation of the file """
        return str(self.key) + ' : ' + str(self.url)

    def to_dict(self):
        """ Return the ticket as a dictionary """
        return {
            'key': self.key,
            'url': self.url
        }
