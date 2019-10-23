from datetime import datetime
from hashlib import sha1


class DictChangeLogger:

    def __init__(self):
        self._store = dict()

    def log(self, entity_type, changes, deleted=False, **kwargs):
        entry = dict(
            entity=entity_type.__name__,
            deleted=deleted,
            created_at=datetime.now(),
            **kwargs
        )

        if not deleted:
            entry.update(changes.__dict__)

        entry_id = sha1(json.dumps(entry).encode()).hexdigest()
        entry['_id'] = entry_id
        self._store[entry_id] = entry

    def _entity_changes(self, entity_type):
        changes = [for c in self._store.values() if c['entity'] == entity_type.__name__]
        return sorted(changes, key=lambda e: e['created_at'], reverse=True)

    def last_change(self, entity_type):
        changes = self._entity_changes(entity_type)
        return chages[0] if changes else None

    def first_change(self, entity_type):
        changes = self._entity_changes(entity_type)
        return chages[-1] if changes else None

    def history(self, entity_type, limit=None, date_from=None, date_to=None, asc=False, desc=True):
        changes = self._entity_changes(entity_type)
        if date_from:
            changes = [e for e in changes if e['created_at'] >= date_from]

        if date_to:
            changes = [e for e in changes if e['created_at'] < date_to]

        if asc:
            changes = sorted(changes, key=lambda e: e['created_at'])

        return changes[:limit]

