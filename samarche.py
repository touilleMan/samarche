from importlib import import_module
import inspect

# Republishing for easy serialization
from pickle import load, loads, dump, dumps  # noqa


def import_string(dotted_path):
    """
    Import a dotted module path or a element from it if a `:` separator
    is provided
    :arg dotted_path: path to import (e.g. 'my_module.my_package:MyClass')
    """
    try:
        module_path, class_name = dotted_path.rsplit(':', 1)
    except ValueError:
        return import_module(dotted_path)
    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        raise ImportError(msg)


def signature_factory(target):
    """
    Create a :class Signature: of the given object
    """
    if inspect.ismodule(target):
        return ModuleSignature(target)
    elif inspect.isclass(target):
        return ClassSignature(target)
    elif inspect.isfunction(target):
        return FunctionSignature(target)
    else:
        return AttributeSignature(target)


class ValidationError(Exception):
    pass


class Signature:
    """
    Representation of a public API
    """

    def __init__(self, target=None):
        if target:
            self.build_signature(target)

    def encode(self):
        raise NotImplementedError

    def build_signature(self, target):
        raise NotImplementedError

    def decode(self):
        raise NotImplementedError

    def validate(self, signature):
        if self.__class__ != signature.__class__:
            return ('type has changed (orginal: `%s`, now: `%s`)' %
                    (self.__class__.__name__, signature.__class__.__name__))

    def __eq__(self, other):
        return self._signature == other._signature


class LeafSignature(Signature):
    def build_signature(self, target):
        pass


class NodeSignature(Signature):
    def __init__(self, *args, **kwargs):
        self._signature = {}
        super().__init__(*args, **kwargs)

    def build_signature(self, target):
        public_attrs = (m for m in dir(target) if not m.startswith('_'))
        for attr in public_attrs:
            self._signature[attr] = signature_factory(getattr(target, attr))

    def validate(self, original):
        errors = super().validate(original)
        if errors:
            return errors
        errors = {}
        original_keys = original._signature.keys()
        keys = self._signature.keys()
        errors.update({m: 'missing element' for m in original_keys - keys})
        errors.update({u: 'unknown element' for u in keys - original_keys})
        for key in original_keys & keys:
            err = self._signature[key].validate(original._signature[key])
            if err:
                errors[key] = err
        if errors:
            return errors


class ModuleSignature(NodeSignature):
    pass


class ClassSignature(NodeSignature):
    pass


class FunctionSignature(LeafSignature):
    def build_signature(self, target):
        self._signature = inspect.getfullargspec(target)

    def validate(self, original):
        errors = super().validate(original)
        if errors:
            return errors
        errors = []
        for elm in ["args", "varargs", "varkw", "defaults",
                    "kwonlyargs", "kwonlydefaults", "annotations"]:
            signature_elm = getattr(self._signature, elm)
            original_elm = getattr(original._signature, elm)
            if (signature_elm != original_elm):
                errors.append('%s ==> original: %s, new: %s'.format(
                    elm, original_elm, signature_elm))
        if errors:
            return "Function signature has changed:\n%s" % '\n'.join(errors)


class AttributeSignature(LeafSignature):
    pass


def build_signature(target_path):
    """
    Generate a :class Signature: representing the element at target_path
    :arg target_path: dotted path to the element, can contain a final `:`
    to point on a package attribute
    """
    target = import_string(target_path)
    return signature_factory(target)


def check_signature(target_path, signature):
    """
    Try to validate the given target object against the :class Signature:
    or raise a :class ValidationError: exception
    :arg target_path: dotted path to the element, can contain a final `:`
    to point on a package attribute
    """
    current = build_signature(target_path)
    errors = current.validate(signature)
    if errors:
        raise ValidationError(errors)
