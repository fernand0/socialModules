from unittest.mock import patch

import pytest

from socialModules.configMod import getApi, getModule


def test_getModule_success():
    # Assuming 'Rss' is a valid module that can be loaded
    module = getModule('Rss')
    assert module is not None

def test_getModule_importerror():
    module = getModule('NonExistentModule')
    assert module is None

@patch('socialModules.configMod.getModule', return_value=None)
def test_getApi_fail(mock_get_module):
    api = getApi('NonExistentModule', 'test_nick')
    assert api is None

# To test AttributeError, we would need to create a dummy module
# without the expected class, which is more involved.
# For now, we'll stick to testing ImportError.

