from .tracker import Tracker


class TrackedEntityManager(Tracker):

    def __init__(self, entity_manager, comparator, change_logger, store=None):
        self.manager = entity_manager
        super(TrackedEntityManager, self).__init__(comparator, change_logger, store)

    def get_by_id(self, _id):
        entity = self.manager.get_by_id(_id)
        self.track_entity(entity)
        return entity

    def get_one(self, query):
        entity = self.manager.get_one(query)
        self.track_entity(entity)
        return entity

    def get_many(self, query):
        for r in self.manager.get_many(query):
            self.track_entity(r)
            yield entity

    def save(self, entity, **log_data):
        self.log_changes(entity, **log_data)
        saved_entity = self.manager.save(entity)
        return saved_entity

    def delete(self, entity, **log_data):
        self.log_changes(entity, deleted=True, **log_data)
        saved_entity = self.manager.delete(entity)
        return saved_entity
