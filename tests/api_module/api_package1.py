
class ApiPackage1Class1:
    def __init__(self, arg1, arg2):
        self.value1 = "value1"

    def public1(self, arg1):
        pass

    def public2(self):
        pass

    @property
    def public_property1(self):
        return self._public_property

    @property
    def public_property2(self):
        return self._public_property2

    @public_property2.setter
    def public_property2(self, value):
        self._public_property2 = value

    def _fake_private(self):
        pass

    def __real_private(self):
        pass


def ApiPackage1_function1():
    pass


def _ApiPackage1_fake_private_function():
    pass


def __ApiPackage1_real_private_function():
    pass
