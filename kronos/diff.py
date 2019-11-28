from .utils import serializable_dict


class Change(object):

    def __init__(self, key, value, old_value=None, **kwargs):
        self.key = key
        self.value = value
        self.old_value = old_value
        self.metadata = kwargs or {}

    def __repr__(self):
        return serializable_dict(self.__dict__)


class Diff(object):

    def __init__(self, field_name=None, diff=None, **kwargs):
        self.field_name = field_name
        self.added = diff.added if diff else []
        self.deleted = diff.deleted if diff else []
        self.updated = diff.updated if diff else []
        self.metadata = kwargs or {}

    @property
    def empty(self):
        return not any([self.added, self.deleted, self.updated])


class DiffHelper(object):

    def _missing_items(self, existing_items, items):
        return [k for k in items if k not in existing_items]

    def value_is_dict_or_entity(self, value):
        return hasattr(value, '__dict__') or isinstance(value, dict)

    def _list_diff(self, field_name, new_value, old_value):
        list_field_diff = Diff(field_name=field_name)

        # If the list elements are dicts or entities, go for an
        # entity diff instead of a diff of simple list of scalars
        if self.value_is_dict_or_entity(new_value[0]):
            new_dict = {e.get('id'): e for e in new_value}
            old_dict = {e.get('id'): e for e in old_value}

            new_ids = set(new_dict.keys())
            old_ids = set(old_dict.keys())

            if new_ids or old_ids:
                added_ids = new_ids.difference(old_ids)
                deleted_ids = old_ids.difference(new_ids)
                common_ids = new_ids.intersection(old_ids)

                for existing_id in common_ids:
                    elem_diff = self.diff(new_dict.get(existing_id), old_dict.get(existing_id))
                    if not elem_diff.empty:
                        list_field_diff.updated.append(elem_diff)

                for new_id in added_ids:
                    list_field_diff.added.append(Change(
                        new_id, value=new_dict.get(new_id), old_value=None)
                    )

                for deleted_id in deleted_ids:
                    list_field_diff.deleted.append(Change(
                        deleted_id, value=None, old_value=old_dict.get(deleted_id))
                    )

        else:
            # Simple list diff where there's only add/delete
            for nv in new_value:
                if nv not in old_value:
                    list_field_diff.added.append(
                        Change(None, value=nv, old_value=None)
                    )

            for ov in old_value:
                if ov not in new_value:
                    list_field_diff.deleted.append(
                        Change(None, value=None, old_value=ov)
                    )

        return list_field_diff

    def diff(self, entity_dict, old_entity_dict, **metadata):
        """
        Calculates the diff between two entity's dicts. When dealing
        with nested entities or fields that are list of entities, in order
        to calculate the diff it assumes every entity dict has an `id` field,
        otherwise calculates the diff as if it were a simple list of scalars

        """
        new_keys = set(entity_dict.keys())
        old_keys = set(old_entity_dict.keys())

        existing_keys = old_keys.intersection(new_keys)

        _diff = Diff(**metadata)

        for new_field in self._missing_items(existing_keys, new_keys):
            _diff.added.append(Change(new_field, entity_dict.get(new_field)))

        for deleted_field in self._missing_items(existing_keys, old_keys):
            _diff.deleted.append(Change(deleted_field, None, old_entity_dict.get(deleted_field)))

        for k in existing_keys:
            new_value, old_value = entity_dict.get(k), old_entity_dict.get(k)

            if isinstance(new_value, (list, set, tuple)):
                list_field_diff = self._list_diff(k, new_value, old_value)

                if not list_field_diff.empty:
                    _diff.updated.append(list_field_diff)

            elif self.value_is_dict_or_entity(new_value):
                sub_entity_diff = self.diff(new_value, old_value)

                if not sub_entity_diff.empty:
                    _diff.updated.append(Diff(
                        field_name=k,
                        diff=sub_entity_diff,
                    ))

            elif new_value != old_value:
                _diff.updated.append(Change(k, value=new_value, old_value=old_value))

        return _diff
