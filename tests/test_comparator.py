import pytest

try:
    from unittest import mock
except:
    import mock

from functools import partial
from collections import OrderedDict

from kronos.comparator import EntityComparator, EntityComparatorError


class Entity:
    def __init__(self, name, first_name, last_name, age, profession, address):
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.profession = profession
        self.address = address

    def to_dict(self):
        return self.__dict__


@pytest.fixture
def dict_entity():
    return dict(
        name='test test',
        first_name='test',
        last_name='test',
        age=30,
        profession='programmer',
        address=dict(
            name='test',
            address1='test address1',
            address2='test address2',
            city='test city',
            state='test state',
            country='test country',
            zip='test zip'
        )
    )

@pytest.fixture
def entity():
    return Entity(
        name='test test',
        first_name='test',
        last_name='test',
        age=30,
        profession='programmer',
        address=dict(
            name='test',
            address1='test address1',
            address2='test address2',
            city='test city',
            state='test state',
            country='test country',
            zip='test zip'
        )
    )

@pytest.fixture
def dummy_comparator(entity):
    comparator_mock = mock.MagicMock()
    comparator_mock.entity_type = Entity
    comparator_mock.entity_to_dict.return_value = {}
    comparator_mock.diff.return_value = {}
    return comparator_mock


def clone_entity(entity, count=2):
    entities = []
    for _ in range(count):
        new_entity = Entity(**entity.__dict__)
        new_entity.address = dict(entity.address)
        entities.append(new_entity)

    return entities


def test_entity_id(entity):
    ec = EntityComparator()
    assert not ec.entity_id(entity)

    entity.id = 'test-id'
    assert 'test-id' == ec.entity_id(entity)


def test_entity_to_dict(entity, dict_entity):
    ec = EntityComparator()

    # A dict is returned as it is...
    assert OrderedDict(dict_entity) == ec.entity_to_dict(dict_entity)

    assert OrderedDict(dict_entity) == ec.entity_to_dict(entity)

    # if no to_dict/as_dict and no comparator defined, then raises error
    mocked_entity = object()

    with pytest.raises(EntityComparatorError):
        ec.entity_to_dict(mocked_entity)

def test_entity_to_dict_with_comparators(entity, dummy_comparator):
    ec = EntityComparator(comparators=[dummy_comparator])
    ec.entity_to_dict(entity)

    dummy_comparator.entity_to_dict.assert_called_once()


def test_diff(entity, dummy_comparator):
    new_entity, old_entity = clone_entity(entity)

    diff_helper = mock.MagicMock()
    diff_helper.diff.return_value = {}

    ec = EntityComparator(diff_helper=diff_helper)

    ec.diff(new_entity, old_entity)

    diff_helper.diff.assert_called_once()


def test_diff_with_comparators(entity, dummy_comparator):
    new_entity, old_entity = clone_entity(entity)

    ec = EntityComparator(comparators=[dummy_comparator])

    ec.diff(new_entity, old_entity)
    dummy_comparator.entity_to_dict.assert_called()
    dummy_comparator.diff.assert_called()
