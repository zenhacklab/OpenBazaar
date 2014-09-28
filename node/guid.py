"""
Author: Nikolaos <renelvon> Korasidis
contact: renelvon@gmail.com
"""

class GUIDMixin(object):
    """
    An interface for a GUID.

    Any class that is meant to be used as a GUID
    should inherit this one.
    """
    def __init__(self, guid):
        self.guid = guid

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.guid == other.guid
        elif isinstance(other, str):
            return self.guid == other
        return False

    def __repr__(self):
        return repr(self.guid)
