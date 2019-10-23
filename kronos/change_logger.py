


class ChangeLogger:

    def log(self, entity_type, changes, created=False, deleted=False, **kwargs):
        raise NotImplementedError

    def last_change(self, entity_type):
        raise NotImplementedError

    def first_change(self, entity_type):
        raise NotImplementedError

    def history(self, entity_type, limit=None, date_from=None, date_to=None, asc=False, desc=True):
        raise NotImplementedError

