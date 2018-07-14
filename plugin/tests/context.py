# Copyright 2017 Kristopher Heijari
#
# This file is part of vim-liq.
#
# vim-liq.is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vim-liq.is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-liq.  If not, see <http://www.gnu.org/licenses/>.

import logging

# format_ = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# logging.basicConfig(level=logging.DEBUG, format=format_)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

log = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

import os
import sys
test_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(test_dir, '..'))

try:
    import unittest.mock as mock
except ImportError:
    import mock

import pytest


# Always mock the vim module otherwise import won't work
sys.modules["vim"] = mock.MagicMock()


@pytest.fixture
def vim_mock():
    # Return the mocked module
    return sys.modules["vim"]


@pytest.fixture
def v_filetype(monkeypatch):
    mock_ = mock.Mock(return_value="python")
    monkeypatch.setattr("vimliq.vimutils.filetype", mock_)
    return mock_


class Partial(str):
    def __eq__(self, other):
        return self in other


import vimliq.client
import vimliq.clientmanager
