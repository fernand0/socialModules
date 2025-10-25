import pytest
from socialModules.configMod import getModule

def test_getModule_success():
    # Assuming 'Rss' is a valid module that can be loaded
    module = getModule('Rss')
    assert module is not None

def test_getModule_importerror():
    with pytest.raises(ModuleNotFoundError):
        getModule('NonExistentModule')


# To test AttributeError, we would need to create a dummy module
# without the expected class, which is more involved.
# For now, we'll stick to testing ImportError.
