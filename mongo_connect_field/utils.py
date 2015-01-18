import importlib
import six


def import_class(cls_path):
    if not isinstance(cls_path, six.string_types):
        return cls_path
    #cls is a module path to string
    if '.' in cls_path:
            # Try to import.
            module_bits = cls_path.split('.')
            module_path, class_name = '.'.join(module_bits[:-1]), module_bits[-1]
            module = importlib.import_module(module_path)
    else:
        # We've got a bare class name here, which won't work (No AppCache
        # to rely on). Try to throw a useful error.
        raise ImportError("Rquires a Python-style path (<module.module.Class>) "
                          "to load given cls. Only given '%s'." % cls_path)

    cls = getattr(module, class_name, None)

    if cls is None:
        raise ImportError("Module '%s' does not appear to have a class called '%s'." % (module_path, class_name))

    return cls
