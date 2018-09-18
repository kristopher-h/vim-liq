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

"""This module tests installation and using the python language serverer "e2e"."""
import shutil
import tempfile
import time

from context import *

# Hackky workaroudn to access MonkeyPatch class in module scoped fixture
# Suggestion taken from here: https://github.com/pytest-dev/pytest/issues/363
from _pytest.monkeypatch import MonkeyPatch

# Line is "one based" while col is "zero based" since vim seems to behave that way. E.g. call
# ":py import vim; vim.current.window.cursor = (4, 4)" jumps to line 4 col 5 (if counting 1 based)
FUNC_LINE = 4
FUNC_COL = 4
FUNC_CALL_LINE = 8
FUNC_CALL_COL = 13
VAR_LINE = 8
VAR_COL = 0
VAR_REF_LINE = 9
VAR_REF_COL = 6


pyls_dir = "servers/python/pyls"
f_type = "python"
f_path = os.path.join(os.path.dirname(__file__), "python_test.py")
f_content = ""
with open(f_path) as f:
    f_content = f.read()


def wait_for(timeout=5):
    stoptime = time.time() + timeout
    while time.time() < stoptime:
        yield
        time.sleep(0.1)


# Override static vim stuff
@pytest.fixture(scope="module")
def vim_static():
    mp = MonkeyPatch()
    mp.setattr("vimliq.vimutils.filetype", mock.Mock(return_value=f_type))
    mp.setattr("vimliq.vimutils.current_file", mock.Mock(return_value=f_path))
    mp.setattr("vimliq.vimutils.current_source", mock.Mock(return_value=f_content))


# This is the client manager used by all tests
@pytest.fixture(scope="module")
def LSP(request, vim_static):
    if not os.path.exists(pyls_dir):
        pytest.skip("No python LSP server installed. run tools/create_release --dev")
    else:
        langserver = {"python": {"cmd": "python " + pyls_dir + " -v --log-file pyls.log", "transport": "STDIO"}}

    log.debug("langserver: %s", langserver)
    client_manager = vimliq.clientmanager.ClientManager(langserver)
    client_manager.add_client()

    for _ in wait_for(8):
        client_manager.process()
        if client_manager.isinitialized:
            print("Initialized")
            break
    else:
        raise Exception("Epic failure")
    client_manager.td_did_open()

    def fin():
        # not using the convinience vim_mock since the scope is module
        sys.modules["vim"].eval.return_value = f_path
        client_manager.td_did_close()
        client_manager.shutdown_all()

    request.addfinalizer(fin)

    return client_manager


def test_did_save(LSP):
    LSP.td_did_save()


def test_did_change(LSP):
    LSP.td_did_change()


def test_definition(LSP, vim_mock):
    vim_mock.current.window.cursor = (FUNC_CALL_LINE, FUNC_CALL_COL)
    LSP.definition()
    exception = None
    for _ in wait_for():
        try:
            LSP.process()
            vim_mock.command.assert_called_with("e {}".format(f_path))
            assert vim_mock.current.window.cursor == (FUNC_LINE, FUNC_COL)
            break
        except AssertionError as exc:
            exception = exc
    else:
        raise exception


def test_reference(LSP, vim_mock):
    vim_mock.current.window.cursor = (VAR_REF_LINE, VAR_REF_COL)
    LSP.references()
    for _ in wait_for():
        try:
            LSP.process()
            print(vim_mock.eval.mock_calls)
            vim_mock.eval.assert_called_with(Partial('"filename":"{}"'.format(f_path)))
            vim_mock.eval.assert_called_with(Partial('"lnum":{}'.format(VAR_LINE)))
            vim_mock.eval.assert_called_with(Partial('"col":{}'.format(VAR_COL)))
            break
        except AssertionError as exc:
            exception = exc
    else:
        raise exception


def test_symbols(LSP, vim_mock):
    LSP.symbols()
    for _ in wait_for():
        try:
            LSP.process()
            vim_mock.eval.assert_any_call(Partial('"text":"a_variable"'))
            vim_mock.eval.assert_any_call(Partial('"text":"a_function"'))
            break
        except AssertionError as exc:
            exception = exc
    else:
        raise exception


def test_completion(LSP, vim_mock, monkeypatch):
    vim_mock.current.window.cursor = (VAR_REF_LINE, VAR_REF_COL + 5)
    result = LSP.completion()
    print(result)
    print(vim_mock.command.mock_calls)
    assert '"word":"a_variable"' in result


def test_diagnostics(LSP, vim_mock):
    vim_mock.eval.return_value = "fake"
    # For now just check the diagnostics list is updated
    for _ in wait_for(10):
        try:
            LSP.process()
            print(LSP.diagnostics)
            assert LSP.diagnostics[f_path][0]["range"]["start"]["line"] == 9
            assert LSP.diagnostics[f_path][0]["message"] == "W391 blank line at end of file"
            break
        except (KeyError, AssertionError) as exc:
            exception = exc
    else:
        raise exception
