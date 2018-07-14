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


"""Test vimliq/client.py."""
import collections

# Import everything exposed in our test context to this scope
from context import *

# Always return filetype python
pytestmark = pytest.mark.usefixtures("v_filetype")


@pytest.fixture(autouse=True)
def v_current_file(monkeypatch):
    mock_ = mock.Mock(return_value="fake.py")
    monkeypatch.setattr("vimliq.vimutils.current_file", mock_)
    return mock_


@pytest.fixture
def client(monkeypatch):
    rpcmock = mock.Mock(spec=vimliq.jsonrpc.JsonRpc)
    iomock = mock.Mock(spec=vimliq.base.StdIO)
    lsp_client = vimliq.client.VimLspClient("start")
    monkeypatch.setattr(lsp_client, "rpc", rpcmock)
    monkeypatch.setattr(lsp_client, "io", iomock)

    return lsp_client


def test_shutdown(client):
    client.shutdown()
    client.io.close.assert_called_once_with()


def test_update_signs(client, monkeypatch, vim_mock):
    monkeypatch.setattr(client, "_next_sign_id", mock.Mock(return_value=9))
    client.update_signs()
    # TODO: uncomment when proper diagnostics
    # vim_mock.command.assert_called_with("sign place 9 line=2 name=LspSign file=fake.py")


def test_display_diagnostics_help(client, monkeypatch, vim_mock):
    vim_mock.current.window.cursor = (2, 2)
    vim_mock.eval.return_value = 50
    client.display_diagnostics_help()
    print(vim_mock.command.calls)
    # TODO: Mock diagnostics in client
    # vim_mock.command.assert_any_call(Partial("fake msg"))


def test_clear_signs(client):
    client.clear_signs()


def test_display_diagnostics(client):
    client.display_diagnostics()


def test_td_did_open(client):
    client.td_did_open()


def test_td_did_change(client):
    client.td_did_change()


def test_td_did_save(client, monkeypatch):
    client.td_did_save()


def test_td_did_close(client):
    client.td_did_close()


def test_references(client):
    client.references()


def test_definition(client):
    client.definition()


def test_symbols(client):
    client.symbols()
