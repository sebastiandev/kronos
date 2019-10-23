

class Change:

    def __init__(self, key, value, old_value=None, **kwargs):
        self.key = key
        self.value = value
        self.old_value = old_value
        self.metadata = kwargs


class Diff:

    def __init__(self, field_name=None, diff=None, **kwargs):
        self.field_name = field_name
        self.added = diff.added if diff else []
        self.deleted = diff.deleted if diff else []
        self.updated = diff.updated if diff else []
        self.metadata = kwargs

    @property
    def empty(self):
        return not any([self.added, self.deleted, self.updated])


class DiffHelper:

    def _missing_items(self, existing_items, items):
        return [k for k in items if k not in existing_items]

    def diff(self, entity_dict, old_entity_dict):
        new_keys = set(entity_dict.keys())
        old_keys = set(old_entity_dict.keys())

        existing_keys = old_keys.intersection(new_keys)

        _diff = Diff()

        for new_field in self._missing_items(existing_keys, new_keys):
            _diff.added.append(Change(new_field, entity_dict.get(new_field)))

        for deleted_field in self._missing_items(existing_keys, old_keys):
            _diff.deleted.append(Change(deleted_field, None, old_entity_dict.get(deleted_field)))

        for k in existing_keys:
            new_value, old_value = entity_dict.get(k), old_entity_dict.get(k)

            if hasattr(new_value, '__dict__') or isinstance(new_value, dict):
                sub_entity_diff = self.diff(new_value, old_value)

                if not sub_entity_diff.empty:
                    _diff.updated.append(Diff(
                        field_name=k,
                        diff=sub_entity_diff,
                    ))

            elif new_value != old_value:
                _diff.updated.append(Change(k, value=new_value, old_value=old_value))

        return _diff
