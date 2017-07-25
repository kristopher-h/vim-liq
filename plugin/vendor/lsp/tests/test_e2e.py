# Copyright 2017 Kristopher Heijari
#
# This file is part of vim-liq.
#
# vim-liq is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vim-liq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-liq.  If not, see <http://www.gnu.org/licenses/>.
import inspect
import logging
import os
import sys
import time

import pytest

from .context import lsp

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="module")
def lsp_pipe():
    thing = lsp.jsonrpc.JsonRpcStdInOut(["pyls"])
    return thing


@pytest.fixture(scope="module")
def lsp_client():
    pipe = lsp.jsonrpc.JsonRpcStdInOut(["pyls"])
    thing = lsp.client.LspClient(pipe)
    return thing


FILE_PATH = os.path.realpath(__file__)
ROOT_PATH = os.path.dirname(FILE_PATH)
FILE_CONTENT = ""
with open(FILE_PATH) as file_:
    FILE_CONTENT = file_.read()


def test_write_read(lsp_pipe):
    response = lsp_pipe.call("initialize", {
        "params": {
            "rootUri": None,
            "rootPath": None,
            "processId": None,
            "processId": None,
            "capabilities": {},
        }
    })
    assert response["result"]


def test_client_initialize(lsp_client):
    assert lsp_client.initialize(root_uri=ROOT_PATH, root_path=ROOT_PATH)["result"]


def test_client_cancel(lsp_client):
    lsp_client.cancel(id=989)


def test_wo_change_configuration(lsp_client):
    lsp_client.wo_did_change_configuration({"aa": "bb"})


def test_wo_symbol(lsp_client):
    response = lsp_client.wo_symbol("test")
    # Method not implemented in pyls server
    assert response["error"]


def test_td_did_open(lsp_client):
    lsp_client.td_did_open(FILE_PATH, "python", 1, FILE_CONTENT)


def test_td_did_change(lsp_client):
    lsp_client.td_did_change(FILE_PATH, 2, FILE_CONTENT)


def test_td_did_save(lsp_client):
    lsp_client.td_did_save(FILE_PATH)


def test_completion(lsp_client):
    class TestComplete():
        test_attr_long = 6
        test_attr = 5
    m_test = TestComplete()
    m_test.test_attr
    line_no = inspect.currentframe().f_lineno - 2

    completion = lsp_client.td_completion(FILE_PATH, line_no, 20)
    assert any(item["label"] == "test_attr_long" for item in completion["result"]["items"])


def test_resolve(lsp_client):
    response = lsp_client.ci_resolve("test_attr")
    # Pyls server does not support method exercise the code anyway
    assert response["error"]


def test_hover(lsp_client):
    class TestComplete():
        """This is a test docstring."""
    m_test = TestComplete()
    line_no = inspect.currentframe().f_lineno - 2

    response = lsp_client.td_hover(FILE_PATH, line_no, 20)
    assert response["result"]["contents"] == "This is a test docstring."


def test_references(lsp_client):
    test_var = "declared"
    orig_line_no = inspect.currentframe().f_lineno - 2

    test_var
    line_no = inspect.currentframe().f_lineno - 2

    response = lsp_client.td_references(FILE_PATH, line_no, 7, True)
    assert response["result"][0]["range"]["start"]["line"] == orig_line_no


def test_signature_help(lsp_client):
    def test_func(arg1, arg2):
        """This is a test func."""

    test_func(1, 2)
    line_no = inspect.currentframe().f_lineno - 2

    response = lsp_client.td_signature_help(FILE_PATH, line_no, 14)
    assert any(
        item["label"] == "test_func(arg1, arg2)" for item in response["result"]["signatures"])


def test_document_highlight(lsp_client):
    var1 = 1
    line_no = inspect.currentframe().f_lineno - 2
    var1 = 2
    response = lsp_client.td_document_highlight(FILE_PATH, line_no, 14)
    # Pyls server does not support method exercise the code anyway
    assert response["error"]


def test_document_symbol(lsp_client):
    response = lsp_client.td_document_symbol(FILE_PATH)
    # Pyls server does not support method exercise the code anyway
    assert response["result"]


def test_formatting(lsp_client):
    response = lsp_client.td_formatting(FILE_PATH, 4, True)
    # Just check a list is returned for now
    assert response["result"][0]


def test_range_formatting(lsp_client):
    response = lsp_client.td_range_formatting(FILE_PATH, 4, True, 0, 3, 0, 5)
    assert response["result"] == []


def test_on_type_formatting(lsp_client):
    test_var = "declared"

    orig_line_no = inspect.currentframe().f_lineno - 2

    response = lsp_client.td_on_type_formatting(FILE_PATH, 4, True, orig_line_no, 4, "    test")
    # Method not implemented in pyls server
    assert response["error"]


def test_definition(lsp_client):
    def test_func():
        pass
    orig_line_no = inspect.currentframe().f_lineno - 3
    test_func()
    func_line_no = inspect.currentframe().f_lineno - 2
    response = lsp_client.td_definition(FILE_PATH, func_line_no, 12)
    assert response["result"][0]["range"]["start"]["line"] == orig_line_no


def test_code_action(lsp_client):
    unused_var = None
    line_no = inspect.currentframe().f_lineno - 2
    response = lsp_client.td_code_action(FILE_PATH, line_no, line_no, 4, 14)
    # Method not implemented in pyls server
    assert response["error"]


def test_code_lens(lsp_client):
    response = lsp_client.td_code_lens(FILE_PATH)
    # Method not implemented in pyls server
    assert response["error"]


def test_document_link(lsp_client):
    response = lsp_client.td_document_link(FILE_PATH)
    # Method not implemented in pyls server
    assert response["error"]


def test_rename(lsp_client):
    variable = None
    line_no = inspect.currentframe().f_lineno - 2
    variable = "renamed_var"
    response = lsp_client.td_rename(FILE_PATH, line_no, 8, variable)
    # Method not implemented in pyls server
    assert response["error"]


def test_td_did_close(lsp_client):
    lsp_client.td_did_close(FILE_PATH)


def test_client_shutdown(lsp_client):
    lsp_client.shutdown()
    print(lsp_client._json_rpc._handler._sync_queue)
    print(lsp_client._json_rpc._handler._async_queue)

    assert not lsp_client.is_alive()
