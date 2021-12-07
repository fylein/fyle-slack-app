app_to_database = {
    'django_cache': 'cache'
}

class CacheRouter:

    def db_for_read(self, model, **hints):
        return app_to_database.get(model._meta.app_label, None)

    def db_for_write(self, model, **hints):
        return app_to_database.get(model._meta.app_label, None)

    def allow_syncdb(self, db, model):
        _db = app_to_database.get(model._meta.app_label, None)
        return db == _db if _db else None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        _db = app_to_database.get(app_label, None)
        return db == _db if _db else None
