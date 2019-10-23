from collections import OrderedDict

from .errors import KronosError
from .diff import DiffHelper


class EntityComparatorError(KronosError):
    pass


class EntityComparator:

    def __init__(self, comparators=None, diff_helper=None):
        self._comparators = comparators or []
        self._diff_helper = diff_helper or DiffHelper()

    def _comparator_for_entity(self, entity):
        for comp in self._comparators:
            if comp.entity_type in (entity.__class__.__name__, entity.__class__):
                return comp

    def entity_id(self, entity):
        return getattr(entity, 'id', None)

    def entity_to_dict(self, entity, use_dict=False):
        comp = self._comparator_for_entity(entity)

        if isinstance(entity, dict):
            d = entity

        elif comp:
            d = comp.entity_to_dict(entity)

        elif hasattr(entity, 'to_dict'):
            d = entity.to_dict()

        elif hasattr(entity, 'as_dict'):
            d = entity.as_dict()

        elif use_dict:
            d = entity.__dict__
            for k, v in d.items():
                if hasattr(v, '__dict__'):
                    d['k'] = self.entity_to_dict(v, use_dict=use_dict)

        else:
            raise EntityComparatorError(
                "Could't convert entity to dict. Entity '{}' should implement " \
                "at least one of to_dict/as_dict methods".format(entity.__class__.__name__)
            )

        return OrderedDict(d)

    def diff(self, entity, old_entity, **kwargs):
        new_entity = entity

        if not isinstance(entity, dict):
            new_entity = self.entity_to_dict(entity)

        if not isinstance(old_entity, dict):
            old_entity = self.entity_to_dict(old_entity)


        comp = self._comparator_for_entity(entity)

        if comp:
            _diff = comp.diff(new_entity, old_entity, **kwargs)

        else:
            _diff = self._diff_helper.diff(new_entity, old_entity, kwargs.get('metadata'))

        return _diff

