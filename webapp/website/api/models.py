from django.db import models

# Create your models here.

class AccessControlList(object):
    def __init__(self, owner, mode, usernames=()):
        if mode not in ('allow', 'block'):
            raise ValueError('mode must be "allow" or "block"')
        self.owner = owner
        self.mode = mode
        self.usernames = set(usernames)

    @staticmethod
    def from_dict(d):
        if any(k not in d for k in ('owner', 'mode', 'usernames')):
            raise ValueError('missing "owner", "mode", or "usernames" field')
        return AccessControlList(d['owner'], d['mode'], d['usernames'])

    def to_dict(self):
        return dict(owner=self.owner, mode=self.mode, usernames=list(self.usernames))

    def is_allowed(self, username):
        if self.owner == username:
            return True
        if self.mode == 'allow':
            return username in self.usernames
        else:
            return username not in self.usernames

    def is_owner(self, username):
        return username == self.owner

    # Useful for unit tests to compare expected values
    def __eq__(self, other):
        if not isinstance(other, AccessControlList):
            return False
        if self.owner != other.owner:
            return False
        if self.mode != other.mode:
            return False
        return self.usernames == other.usernames

    def __ne__(self, other):
        return not self == other
