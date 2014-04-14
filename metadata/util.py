from __future__ import absolute_import


def get_value(d, *keys):
    return reduce(lambda a, b: a[b], keys, d)


def first_item(l):
    """Returns first item in the list or None if empty."""
    return l[0] if len(l) > 0 else None


class cache(object):
    '''Computes attribute value and caches it in the instance.
    Python Cookbook (Denis Otkidach)
        http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once
    and accessed many times. Sort of like memoization.
    '''
    def __init__(self, method, name=None):
        # record the unbound-method and the name
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self
        # compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't get called
        # again
        setattr(inst, self.name, result)
        return result
