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
from .context import *

# Always return filetype python
pytestmark = pytest.mark.usefixtures("v_filetype")


@pytest.fixture(autouse=True)
def v_current_file(monkeypatch):
    mock_ = mock.Mock(return_value="fake.py")
    monkeypatch.setattr("vimliq.vimutils.current_file", mock_)
    return mock_


@pytest.fixture
def client(monkeypatch):
    mock_client = mock.Mock()
    lsp_client = vimliq.client.VimLspClient("start", "transport")
    monkeypatch.setattr(lsp_client, "_client", mock_client)

    # Add sane diagnostics
    mock_diag = mock.Mock()
    mock_diag.start_line = 1
    mock_diag.message = "fake msg"
    mock_diag.uri = "fake.py"
    mock_diag.start_char = 9
    monkeypatch.setattr(lsp_client, "diagnostics", {"fake.py": [mock_diag]})
    return lsp_client


def test_shutdown(client):
    client.shutdown()
    client._client.shutdown.assert_called_once_with()


def test_update_signs(client, monkeypatch, vim_mock):
    monkeypatch.setattr(client, "_next_sign_id", mock.Mock(return_value=9))
    client.update_signs()
    vim_mock.command.assert_called_with("sign place 9 line=2 name=LspSign file=fake.py")


def test_display_sign_help(client, monkeypatch, vim_mock):
    vim_mock.current.window.cursor = (2, 2)
    vim_mock.eval.return_value = 50
    client.display_sign_help()
    print(vim_mock.command.calls)
    vim_mock.command.assert_any_call(Partial("fake msg"))


def test_clear_signs(client):
    client.clear_signs()


def test_process_diagnostics(client):
    diag_mock = mock.Mock()
    diag_mock.diagnostics = "fake"
    diag_mock.uri = "2fake.py"
    client._client.diagnostics.return_value = [diag_mock]
    client.process_diagnostics()
    assert client.diagnostics["2fake.py"] == "fake"


def test_display_diagnostics(client):
    client.display_diagnostics()


def test_td_did_open(client):
    client.td_did_open()


def test_td_did_change(client):
    client.td_did_change()


def test_td_did_save(client, monkeypatch):
    monkeypatch.setattr(client, "process_diagnostics", mock.Mock())
    client.td_did_save()


def test_td_did_close(client):
    client.td_did_close()


Location = collections.namedtuple("Location", ["uri", "start_char", "start_line"])

def test_td_references(client):
    client._client.td_references.return_value = [Location("fake", 1, 2)]
    client.td_references()


def test_td_definition(client):
    client._client.td_definition.return_value = [Location("fake", 1, 2)]
    client.td_definition()


def test_td_symbols(client):
    client._client.td_document_symbol.return_value = [Location("fake", 1, 2)]
    client.td_symbols()

Completion = collections.namedtuple("Completion", ["label", "kind", "detail", "documentation"])

def test_completion(client, monkeypatch):
    monkeypatch.setattr("vimliq.client.omni_add_base", mock.Mock(return_value=("test", "fake")))
    client._client.td_completion.return_value = [Completion("fake", 1, 2, 3)]
    client.td_completion()
