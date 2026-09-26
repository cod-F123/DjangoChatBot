from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _

# Create your models here.


class UserManager(BaseUserManager):
    """
    This class defines manager for the user model
    """

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError(_("Users must have an email address"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    This class defines the user model
    """

    email = models.EmailField(
        verbose_name=_("email"), max_length=255, unique=True
    )
    is_active = models.BooleanField(verbose_name=_("is active"), default=True)
    is_staff = models.BooleanField(verbose_name=_("is staff"), default=False)
    is_superuser = models.BooleanField(
        verbose_name=_("is superuser"), default=False
    )
    is_verified = models.BooleanField(
        verbose_name=_("is verified"), default=False
    )

    created_date = models.DateTimeField(
        verbose_name=_("created date"), auto_now_add=True
    )
    updated_date = models.DateTimeField(
        verbose_name=_("updated_date"), auto_now=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
