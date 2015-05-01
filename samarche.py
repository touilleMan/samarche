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
    elif inspect.isgenerator(target) or inspect.isgeneratorfunction(target):
        return GeneratorSignature(target)
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

    def __str__(self):
        raise NotImplementedError

    def build_signature(self, target):
        self._name = target.__name__

    def validate(self, signature):
        if self.__class__ != signature.__class__:
            return ('type mismatch (orginal: %s, actual: %s)' %
                    (self, signature))

    def __eq__(self, other):
        return not self.validate(other)


class LeafSignature(Signature):
    pass


class NodeSignature(Signature):

    def __init__(self, *args, **kwargs):
        self._signature = {}
        super().__init__(*args, **kwargs)

    def build_signature(self, target):
        super().build_signature(target)
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
        errors.update({str(original._signature[m]): 'missing element'
                       for m in original_keys - keys})
        errors.update({str(self._signature[u]): 'unknown element'
                       for u in keys - original_keys})
        for key in original_keys & keys:
            err = self._signature[key].validate(original._signature[key])
            if err:
                errors[str(self._signature[key])] = err
        if errors:
            return errors


class ModuleSignature(NodeSignature):

    def __str__(self):
        return 'Module %s' % self._name


class ClassSignature(NodeSignature):

    def __str__(self):
        return 'Class %s' % self._name


class FunctionSignature(LeafSignature):

    def __init__(self, *args, **kwargs):
        self._built_in_function = False
        self._signature = None
        super().__init__(*args, **kwargs)

    def build_signature(self, target):
        super().build_signature(target)
        self._built_in_function = False
        self._signature = None
        try:
            argspec = inspect.getfullargspec(target)
            self._signature = {
                "args": argspec.args,
                "varargs": argspec.varargs,
                "varkw": argspec.varkw,
                "kwonlyargs": argspec.kwonlyargs
            }
            if argspec.defaults:
                if isinstance(argspec.defaults, list):
                    self._signature["defaults"] = (signature_factory(d)
                                                   for d in argspec.defaults)
                else:
                    self._signature["defaults"] = signature_factory(
                        argspec.defaults)
            if argspec.kwonlydefaults:
                self._signature["kwonlydefaults"] = {
                    k: signature_factory(v)
                    for k, v in argspec.kwonlydefaults.items()}
            if argspec.annotations:
                self._signature["annotations"] = {
                    k: signature_factory(v)
                    for k, v in argspec.annotations.items()}
            # Serialize params
        except TypeError:
            # Cannot use metaprogramming on C functions
            self._built_in_function = True

    def __str__(self):
        if self._built_in_function:
            return 'Function %s <built-in function>' % self._name
        else:
            return 'Function %s (%s)' % (self._name, self._signature)

    def validate(self, original):
        errors = super().validate(original)
        if errors:
            return errors
        if (self._built_in_function != original._built_in_function or
                self._signature != original._signature):
            return ("Function signature has changed, original: %s, actual %s" %
                    (self, original))


class AttributeSignature(LeafSignature):

    def __init__(self, *args, **kwargs):
        self._type = None
        super().__init__(*args, **kwargs)

    def build_signature(self, target):
        self._type = type(target).__name__

    def validate(self, original):
        errors = super().validate(original)
        if errors:
            return errors
        if self._type != original._type:
            return ("Attribute type has changed: original %s, actual %s" %
                    (self._type, original._type))

    def __str__(self):
        return 'Attribute'


class GeneratorSignature(LeafSignature):

    def __str__(self):
        return 'Generator'


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
