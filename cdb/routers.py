class CdbRouter(object):
    """
    A router to control all database operations on models of the IAS Core
    configuration database.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read config database models go to cdb.
        """
        if model._meta.app_label == 'cdb':
            return 'cdb'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write config database models go to cdb.
        """
        if model._meta.app_label == 'cdb':
            return 'cdb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations only between config database models.
        """
        if obj1._meta.app_label == 'cdb' and \
           obj2._meta.app_label == 'cdb':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the config database data only appears in the 'cdb'
        database.
        """
        if app_label == 'cdb':
            return db == 'cdb'
        else:
            return db == 'default'
        return None
