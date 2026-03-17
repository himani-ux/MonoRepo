from .settings import *  # noqa: F403
from .settings import BASE_DIR


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

UPLOAD_BASE_PATH = str(BASE_DIR / "test_uploads")
PSC_UPLOAD_PATH = UPLOAD_BASE_PATH

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
