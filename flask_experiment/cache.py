from flask import request
from jinja2.utils import LRUCache


class ExperimentTemplateCache(LRUCache):
    def experiment_key(self, key):
        if request.exp_enabled:
            key = ":".join(["{}:{}".format(
                exp.name, var.name) for exp, var in request.experiments.iteritems()]) + ":" + key

        return key

    def __contains__(self, key):
        """Check if a key exists in this cache."""
        #print "Calling parent for contains", self.experiment_key(key)
        return LRUCache.contains(self, self.experiment_key(key))

    def __getitem__(self, key):
        """Get an item from the cache. Moves the item up so that it has the
        highest priority then.

        Raise an `KeyError` if it does not exist.
        """
        #print "Calling parent for __get__", self.experiment_key(key)
        #print self._mapping
        return LRUCache.__getitem__(self, self.experiment_key(key))

    def __setitem__(self, key, value):
        """Sets the value for an item. Moves the item up so that it
        has the highest priority then.
        """
        #print "Calling parent for __set__", self.experiment_key(key)
        return LRUCache.__setitem__(self, self.experiment_key(key), value)

    def __delitem__(self, key):
        """Remove an item from the cache dict.
        Raise an `KeyError` if it does not exist.
        """
        return LRUCache.__delitem__(self, self.experiment_key(key))
