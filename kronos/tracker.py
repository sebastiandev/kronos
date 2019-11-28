import json

from hashlib import sha1

from .errors import KronosError
from .dict_store import DictStore


class EntityConflictError(KronosError):
    pass


class Tracker(object):

    """
    This class allows you to track the state of a given entity. By recording the state in
    a given moment, later on we can get the changes of the current state compared to the
    originally tracked state and keep a record of those change by logging them
    """

    def __init__(self, comparator, change_logger, store=None):
        """
        Builds a tracker

        Parameters:
          - comparator (object): An object used to compare entities.
                The comparator should implement:
                  - entity_to_dict (optional): Converts an entity to dict
                  - diff (required): Builds the diff from two different entity's snapshots

          - change_logger (object): The object in charge of keeping a record
                of the entity's changes. The logger should implement:
                  - log (required): The method that stores the change records for the entity

          - store (object, optional): The backend used to store the entities snapshots
                used for comparisson. The store should implement:
                  - has_key (required): Method to check for existence of a key
                  - get (required): Method to retrieve the value of a key
                  - save (required): Method to save a key/value pair
        """
        self.comparator = comparator
        self.change_logger = change_logger
        self._store = store or DictStore()

    def _entity_id(self, entity, entity_dict):
        _id = None

        if getattr(self.comparator, 'entity_id'):
            _id = self.comparator.entity_id(entity)

        if not _id:
            auto_generated_id = sha1(json.dumps(entity_dict).encode()).hexdigest()
            _id = getattr(entity, 'id', auto_generated_id)

        return _id

    def _build_entity_key(self, entity, entity_dict):
        return "{}-{}".format(entity.__class__.__name__, self._entity_id(entity, entity_dict))

    def track_entity(self, entity, override=False):
        """
        Start tracking the state of an entity. This method will take a snapshot
        of the entity to be used later to compare the state and determine if there
        were any changes applied to the entity.

        Parameters:
          - entity (object): The entity to keep track of
          - override (bool): Skip any checks for a current snapshot of the entity and
                             override it with the current one
        """
        entity_dict = self.comparator.entity_to_dict(entity)

        entity_key = self._build_entity_key(entity, entity_dict)

        if not override and self._store.has_key(entity_key):
            if self._store.get(entity_key) != entity_dict:
                raise EntityConflictError(
                    "The entity is already been tracked and has changes. " \
                    "Save it to track those changes or log the current changes first"
                )

        self._store.save(entity_key, entity_dict)

    def get_entity_diff(self, entity):
        """
        Based on the current entity, looks for previously tracked snapshots
        to calculate the diffs

        Parameters:
          - entity (object): The entity to calculate the diff for

        Returns:
          A Diff object
        """
        diff = None

        entity_dict = self.comparator.entity_to_dict(entity)
        tracked_entity = self._store.get(self._build_entity_key(entity, entity_dict))

        if tracked_entity:
            diff = self.comparator.diff(entity, tracked_entity)

        return diff

    def log_changes(self, entity, created=False, deleted=False, **log_data):
        """
        Given an entity, logs any existing changes between the current state
        and the previously tracked snapshot

        Once changes are logged, the entity's snapshot is updated with the current
        state to start tracking new changes.


        Parameters:
          - entity (object): The entity to log changes for
          - created (bool, optional): If the entity is been created. In this case
                there will be no previous snapshot, so diff is the current snapshot
          - deleted (bool, optional): If the entity is been deleted. In this case
                there will be no diff
          - log_data (dict, optional): An extra metadata to be included in the change logs

        Returns:
          A Diff object representing the change from the current state and the previously
          tracked snapshot
        """
        diff = None

        if created:
            diff = self.comparator.diff(entity, {})
            self.change_logger.log(entity, diff, created=created, **log_data)

        elif deleted:
            self.change_logger.log(entity, None, deleted=deleted, **log_data)

        else:
            diff = self.get_entity_diff(entity)

            if diff:
                self.change_logger.log(entity, diff, **log_data)
                # update the tracked entity with the latest state
                self.track_entity(entity, override=True)

        return diff
