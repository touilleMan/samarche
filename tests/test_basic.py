import pytest
import samarche
from importlib import reload


def test_basic():
    targets = [
        "api_module",
        "api_module.api_package1",
        "api_module.api_package1:ApiPackage1_function1",
        "api_module.api_package1:ApiPackage1Class1"
    ]
    for target in targets:
        signature = samarche.build_signature(target)
        samarche.check_signature(target, signature)


def test_bad_check_signature():
    module_signature = samarche.build_signature("api_module")
    with pytest.raises(samarche.ValidationError):
        samarche.check_signature("api_module.api_package1", module_signature)


def test_bad_route():
    bad_routes = [
        "bad_module",
        "api_module.bad_package",
        "api_module.api_package1:BadClass"
    ]
    for bad_route in bad_routes:
        with pytest.raises(ImportError):
            samarche.build_signature(bad_route)


class BaseTest:

    def setup(self):
        self.original_signature = samarche.build_signature("api_module")
        # TODO : reload doesn't clean changed on the module,
        # have to do it by hand in each test...
        import api_module
        reload(api_module)
        self.api_module = api_module


class TestSaveLoad(BaseTest):
    def test_save(self):
        dumped = samarche.dumps(self.original_signature)
        loaded_signature = samarche.loads(dumped)
        assert not loaded_signature.validate(self.original_signature)
    

class TestChangingApi(BaseTest):

    def test_add_func(self):
        self.api_module.api_package1.new_func = lambda x: x
        signature = samarche.signature_factory(self.api_module)
        errors = signature.validate(self.original_signature)
        assert errors
        del self.api_module.api_package1.new_func

    def test_add_cls(self):
        class NewClass:
            pass
        self.api_module.api_package1.NewClass = NewClass
        signature = samarche.signature_factory(self.api_module)
        errors = signature.validate(self.original_signature)
        assert errors
        del self.api_module.api_package1.NewClass

    def test_remove_package(self):
        saved = self.api_module.api_package1
        del self.api_module.api_package1
        signature = samarche.signature_factory(self.api_module)
        errors = signature.validate(self.original_signature)
        assert errors
        self.api_module.api_package1 = saved

    def test_remove_cls(self):
        saved = self.api_module.api_package1.ApiPackage1Class1
        del self.api_module.api_package1.ApiPackage1Class1
        signature = samarche.signature_factory(self.api_module)
        errors = signature.validate(self.original_signature)
        assert errors
        self.api_module.api_package1.ApiPackage1Class1 = saved

    def test_multiple_changes(self):
        saved1 = self.api_module.api_package1.ApiPackage1Class1
        del self.api_module.api_package1.ApiPackage1Class1
        self.api_module.api_package1.new_var = 'new_var'
        self.api_module.api_package2 = self.api_module.api_package1        
        signature = samarche.signature_factory(self.api_module)
        errors = signature.validate(self.original_signature)
        assert errors
        assert len(errors['api_package1']) == 2
        print(errors)
        self.api_module.api_package1.ApiPackage1Class1 = saved1
        del self.api_module.api_package1.new_var
        del self.api_module.api_package2
