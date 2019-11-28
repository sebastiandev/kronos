import pytest

from kronos.diff import DiffHelper, Diff, Change


@pytest.fixture
def entity():
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


def clone_entity(entity, count=2):
    entities = []
    for _ in range(count):
        new_entity = dict(entity)
        new_entity['address'] = dict(entity['address'])
        entities.append(new_entity)

    return entities


def assert_change(change, expected_key, expected_value, expected_old_value):
    if isinstance(change, Change):
        assert expected_key == change.key
        assert expected_value == change.value
        assert expected_old_value == change.old_value

    else:
        raise TypeError("Expected change to be a {} type".format(Change.__name__))


def assert_diff(diff, action, changes, expected_field_name=None):
    if isinstance(diff, Diff):
        if expected_field_name:
            assert expected_field_name == diff.field_name

        if action == 'added':
            items = diff.added
        elif action == 'deleted':
            items = diff.deleted
        elif action == 'updated':
            items = diff.updated

        items = sorted(items, key=lambda e: e.key)
        changes = sorted(changes, key=lambda e: e['expected_key'])

        assert len(items) == len(changes)

        for i in range(len(items)):
            assert_change(items[i], **changes[i])

    else:
        raise TypeError("Expected diff to be a {} type".format(Diff.__name__))


def test_missing_fields(entity):
    new_address = dict(entity['address'])
    old_address = dict(entity['address'])

    new_address.pop('address2')

    common_address_items = set(old_address.keys()).intersection(set(new_address.keys()))

    # The existing items in both, don't include the 'address2' from old_entity
    missing = DiffHelper()._missing_items(common_address_items, old_address.keys())
    assert 1 == len(missing)
    assert 'address2' in missing

    # new_entity has all the fields from old_entity except address2
    missing = DiffHelper()._missing_items(common_address_items, new_address.keys())
    assert not missing


def test_new_fields(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity['favourite color'] = "black"

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.updated
    assert diff.added
    assert 1 == len(diff.added)
    assert_change(diff.added[0], 'favourite color', 'black', None)


def test_deleted_fields(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity.pop('age')

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.updated
    assert not diff.added
    assert 1 == len(diff.deleted)
    assert_change(diff.deleted[0], 'age', None, 30)


def test_updated_fields(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity['age'] = 40
    new_entity['first_name'] = 'new name'

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.added
    assert not diff.deleted
    assert 2 == len(diff.updated)

    diff.updated = sorted(diff.updated, key=lambda e: e.key)

    assert_change(diff.updated[0], 'age', 40, 30)
    assert_change(diff.updated[1], 'first_name', 'new name', 'test')


def test_new_fields_in_embeded_entity(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity['address']['new_field'] = "test"

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added

    assert 1 == len(diff.updated)
    assert isinstance(diff.updated[0], Diff)

    assert_diff(
        diff.updated[0],
        action='added',
        expected_field_name='address',
        changes=[dict(expected_key='new_field', expected_value='test', expected_old_value=None)]
    )

    # No deletes
    assert_diff(
        diff.updated[0],
        action='deleted',
        expected_field_name='address',
        changes=[]
    )

    # No updates
    assert_diff(
        diff.updated[0],
        action='updated',
        expected_field_name='address',
        changes=[]
    )

def test_deleted_fields_in_embeded_entity(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity['address'].pop('address2')

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added

    assert 1 == len(diff.updated)
    assert isinstance(diff.updated[0], Diff)

    # No deletes
    assert_diff(
        diff.updated[0],
        action='deleted',
        expected_field_name='address',
        changes=[dict(expected_key='address2', expected_value=None, expected_old_value='test address2')]
    )

    # No adds
    assert_diff(
        diff.updated[0],
        action='added',
        expected_field_name='address',
        changes=[]
    )

    # No updates
    assert_diff(
        diff.updated[0],
        action='updated',
        expected_field_name='address',
        changes=[]
    )

def test_updated_fields_in_embeded_entity(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity['address']['address2'] = 'new value'

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added

    assert 1 == len(diff.updated)
    assert isinstance(diff.updated[0], Diff)

    assert_diff(
        diff.updated[0],
        action='updated',
        expected_field_name='address',
        changes=[dict(expected_key='address2', expected_value='new value', expected_old_value='test address2')]
    )

    # No deletes
    assert_diff(
        diff.updated[0],
        action='deleted',
        expected_field_name='address',
        changes=[]
    )

    # No adds
    assert_diff(
        diff.updated[0],
        action='added',
        expected_field_name='address',
        changes=[]
    )


def test_new_elements_in_list_field(entity):
    new_entity, old_entity = clone_entity(entity)

    old_entity['tags'] = ["tag1"]
    new_entity['tags'] = ["tag1", "tag2"]

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added
    assert diff.updated
    assert 1 == len(diff.updated)

    assert_diff(
        diff.updated[0],
        action='added',
        expected_field_name='tags',
        changes=[dict(expected_key=None, expected_value='tag2', expected_old_value=None)]
    )


def test_deleted_elements_in_list_field(entity):
    new_entity, old_entity = clone_entity(entity)

    old_entity['tags'] = ["tag1", "tag2"]
    new_entity['tags'] = ["tag1"]

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added
    assert diff.updated
    assert 1 == len(diff.updated)

    assert_diff(
        diff.updated[0],
        action='deleted',
        expected_field_name='tags',
        changes=[dict(expected_key=None, expected_value=None, expected_old_value='tag2')]
    )


def test_updated_entity_in_list_field(entity):
    new_entity, old_entity = clone_entity(entity)

    old_entity['related_entities'] = [dict(id=1, name='test', value='test')]
    new_entity['related_entities'] = [dict(id=1, name='test', value='new value')]

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added
    assert diff.updated
    assert 1 == len(diff.updated)
    assert isinstance(diff.updated[0], Diff)
    assert not diff.updated[0].added
    assert not diff.updated[0].deleted
    assert diff.updated[0].updated

    assert_diff(
        diff.updated[0].updated[0],
        action='updated',
        changes=[dict(expected_key='value', expected_value='new value', expected_old_value='test')]
    )


def test_added_entity_in_list_field(entity):
    new_entity, old_entity = clone_entity(entity)

    old_entity['related_entities'] = [dict(id=1, name='test', value='test')]
    new_entity['related_entities'] = [
        dict(id=1, name='test', value='test'),
        dict(id=2, name='test2', value='test2')
    ]

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added
    assert diff.updated
    assert 1 == len(diff.updated)
    assert isinstance(diff.updated[0], Diff)
    assert not diff.updated[0].updated
    assert not diff.updated[0].deleted
    assert diff.updated[0].added

    assert_diff(
        diff.updated[0],
        action='added',
        changes=[dict(
            expected_key=2,
            expected_value=dict(id=2, name='test2', value='test2'),
            expected_old_value=None
            )
        ]
    )


def test_deleted_entity_in_list_field(entity):
    new_entity, old_entity = clone_entity(entity)

    new_entity['related_entities'] = [dict(id=1, name='test', value='test')]
    old_entity['related_entities'] = [
        dict(id=1, name='test', value='test'),
        dict(id=2, name='test2', value='test2')
    ]

    diff = DiffHelper().diff(new_entity, old_entity)

    assert diff
    assert not diff.empty
    assert not diff.deleted
    assert not diff.added
    assert diff.updated
    assert 1 == len(diff.updated)
    assert isinstance(diff.updated[0], Diff)
    assert not diff.updated[0].updated
    assert not diff.updated[0].added
    assert diff.updated[0].deleted

    assert_diff(
        diff.updated[0],
        action='deleted',
        changes=[dict(
            expected_key=2,
            expected_value=None,
            expected_old_value=dict(id=2, name='test2', value='test2')
            )
        ]
    )
