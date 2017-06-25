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

"""Test vimliq/clientmanager.py."""

# Import everything exposed in our test context to this scope
from .context import *

@pytest.fixture
def v_filetype(monkeypatch):
    mock_ = mock.Mock(return_value="python")
    monkeypatch.setattr("vimliq.vimutils.filetype", mock_)
    return mock_


@pytest.mark.parametrize("value,expected", [
    ({"python": None}, True),
    ({}, False)
])
def test_ClientManager_lang_supported(v_filetype, value, expected):
    manager = vimliq.clientmanager.ClientManager(value)
    assert manager.lang_supported() is expected


PYTHON_CLIENT = {"python": {"start_cmd": "start", "transport": "trans", "log_arg": "-a"}}


@pytest.mark.parametrize("log,expected", [
    ("1", ["start", "-a", mock.ANY]),
    ("0", ["start"])
])
def test_ClientManager_add_client(v_filetype, monkeypatch, vim_mock, log, expected):
    vim_mock.eval.return_value = log
    mock_ = mock.MagicMock()
    monkeypatch.setattr("vimliq.client.VimLspClient", mock_)
    manager = vimliq.clientmanager.ClientManager(PYTHON_CLIENT)
    assert not manager.clients
    manager.add_client()
    assert manager.clients["python"]
    mock_.assert_called_once_with(expected, "trans")
    mock_().start_server.assert_called_once_with()


def test_ClientManager_shutdown():
    client_1 = mock.Mock()
    client_2 = mock.Mock()
    manager = vimliq.clientmanager.ClientManager(PYTHON_CLIENT)
    manager.clients = {"client_1": client_1, "client_2": client_2}
    manager.shutdown_all()
    for client in [client_1, client_2]:
        client.shutdown.assert_called_once_with()
