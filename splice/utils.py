import inspect
import functools


def get_class(method):
    """
    Get the class that defines the called function/method.
    It is unlikely that we encounter all cases defined
    below, but just for completeness:
    https://stackoverflow.com/a/25959545/9632613.
    """
    # If the method is a partial function
    if isinstance(method, functools.partial):
        return get_class(method.func)
    # If it is a method (bounded to a class)
    if inspect.ismethod(method) or \
        (inspect.isbuiltin(method) and
         getattr(method, '__self__', None) is not None and
         getattr(method.__self__, '__class__', None)):
        for cls in inspect.getmro(method.__self__.__class__):
            if method.__name__ in cls.__dict__:
                return cls
        method = getattr(method, '__func__', method)  # fallback to __qualname__ parsing
    if inspect.isfunction(method):
        cls = getattr(inspect.getmodule(method),
                      method.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0], None)
        if isinstance(cls, type):
            return cls
    return getattr(method, '__objclass__', None)  # handle special descriptor objects


# Ref: https://gist.github.com/MacHu-GWU/0170849f693aa5f8d129aa03fc358305
# Ref: https://stackoverflow.com/a/50434815/9632613
# Ref: https://stackoverflow.com/a/37147128/9632613
def is_static_method(klass, method_name):
    """Check if a method is @staticmethod. However, this does not work for built-in types."""
    for cls in inspect.getmro(klass):
        if method_name in cls.__dict__:
            return isinstance(inspect.getattr_static(cls, method_name), staticmethod)
    return False


def is_class_method(klass, method_name):
    """Check if a method is @classmethod. However, this does not work for built-in types."""
    if klass.__name__ == 'SpliceInt':
        if method_name == 'from_bytes':
            return True
    for cls in inspect.getmro(klass):
        if method_name in cls.__dict__:
            return isinstance(inspect.getattr_static(cls, method_name), classmethod)
    return False
