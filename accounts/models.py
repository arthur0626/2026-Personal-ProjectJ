from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Canonical identity shared by native and future social authentication."""
