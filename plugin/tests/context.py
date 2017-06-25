import logging
import os
import sys
test_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(test_dir, '..'))
sys.path.insert(0, os.path.join(test_dir, '../vendor/lsp_client_py'))

try:
    import unittest.mock as mock
except ImportError:
    import mock

import pytest


logging.basicConfig(level=logging.DEBUG)

# Always mock the vim module otherwise import won't work
sys.modules["vim"] = mock.MagicMock()


@pytest.fixture
def vim_mock():
    # Return the mocked module
    return sys.modules["vim"]


import vimliq.client
import vimliq.clientmanager
