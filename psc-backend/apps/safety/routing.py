class SafetyRouter:
    """Route Safety ORM traffic to the platform default database alias."""

    safety_app = "safety"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.safety_app:
            return "default"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.safety_app:
            return "default"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.safety_app:
            return db == "default"
        return None
