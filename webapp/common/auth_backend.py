# Copyright (C) 2020 Stefan Hajnoczi <stefanha@gmail.com>
#
# The default ModelBackend only looks up User objects by username.  Many people
# expect to be able to log in with their email address and are confused when
# their credentials are rejected.  This class checks the email address field
# and can be added as an additional authentication backend that will be checked
# if the built-in ModelBackend fails.

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailModelBackend(ModelBackend):
    """
    Authenticates with the email address instead of the username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get(**{UserModel.EMAIL_FIELD: username})
        except (UserModel.DoesNotExist, UserModel.MultipleObjectsReturned):
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
