# Copyright 2017 Kristopher Heijari
#
# This file is part of vim-lsp.
#
# vim-lsp is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vim-lsp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-lsp.  If not, see <http://www.gnu.org/licenses/>.
"""Lsp client lib."""

# TODO: Fix the return types of all functions or change approach to autogenerate the protocol.
#       Right now a lot needs to be kept up to date with the lsp specification. Changing approach
#       would probably make it a bit more combersome for the "calling" code...

import collections
import json
import logging
import os
import sys
try:
    import Queue as queue
except:
    import queue  # py3

from . import jsonrpc

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class LspError(Exception):
    """Error thrown if server replies with an error."""
    def __init__(self, message, code, data=None):
        super(Exception, self).__init__(message)
        self.code = code
        self.data = data


class LspClient(object):
    """Client implementing language server protocol v2.

    https://github.com/Microsoft/language-server-protocol/blob/master/versions/protocol-2-x.md

    """
    def __init__(self, start_cmd, rpc_class=jsonrpc.JsonRpcStdInOut, timeout=2):
        """Create an LspClient.
        Args:
            json_rpc (JsonRpcBase): Class used for reading and writing to remote lsp server.
        """
        self._json_rpc = rpc_class(start_cmd, msg_handler=self.server_callback)
        self.timeout = timeout
        self._proc_id = os.getpid()
        self._server_capabilities = None
        self._msg_queue = queue.Queue()

    # Return types
    # TODO: Fix proper classes?
    # To avoid all to much nesting the return types are flattened compared to the lsp
    # protocol. Similar to what is done for the function calls...

    # For td_definition, td_references
    Location = collections.namedtuple(
        "Location", ["uri", "start_line", "end_line", "start_char", "end_char", "raw"])

    Completion = collections.namedtuple(
        "Completion", ["label", "kind", "detail", "documentation", "raw"])

    # A symbol is a suprset of a Location
    Symbol = collections.namedtuple(
        "Symbol", ["name", "kind", "container_name", "uri", "start_line", "end_line",
                   "start_char", "end_char", "raw"])

    Diagnostic = collections.namedtuple("Diagnostic", ["uri", "diagnostics"])
    DiagnosticItem = collections.namedtuple(
        "DiagnosticItem", ["severity", "code", "source", "message",
                           "start_line", "end_line", "start_char", "end_char", "raw"])
    # End return types

    def diagnostics(self):
        diags = []
        try:
            while True:
                diags.append(self._msg_queue.get(block=False))
        except queue.Empty:
            pass
        return diags

    def server_callback(self, msg):
        """This is a callback function called by tje LspClient read thread.

        This function must not take a long time to finish its stuff, since that would block
        the read thread.
        """
        if self._msg_queue.qsize() > 10:
            # Pop a message from the queue
            self._msg_queue.get()

        try:
            diags = msg["params"]["diagnostics"]
            uri = msg["params"]["uri"]
            diagnostic = LspClient.Diagnostic(uri, [])
            diagnostic_items = [LspClient.DiagnosticItem(
                rd.get("severity", 4),
                rd.get("code", ""),
                rd.get("source", ""),
                rd["message"],
                rd["range"]["start"]["line"],
                rd["range"]["end"]["line"],
                rd["range"]["start"]["character"],
                rd["range"]["end"]["character"],
                msg) for rd in diags]
            diagnostic.diagnostics.extend(diagnostic_items)
            self._msg_queue.put(diagnostic)
        # If it is not a valid diagnostic message
        except KeyError as exc:
            log.debug(exc)
            log.debug("Invalid diagnostic, dropping msg: %s", msg)

    def is_alive(self):
        return self._json_rpc.is_alive()

    # General requests
    def initialize(self, root_uri=None, root_path=None, capabilities={}):
        """Send initialize request.

        Args:
            root_uri (str):
            root_path (str):
            capabilities (dict):
        """
        request = {
            "rootUri": root_uri,
            "rootPath": root_path,
            "processId": self._proc_id,
            "capabilities": capabilities,
        }
        response = self._json_rpc.call("initialize", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        self._server_capabilities = response["result"]
        return response

    def initialized(self):
        """Send initialized notification."""
        self._json_rpc.notify("initialized", None)

    def shutdown(self):
        """Send shutdown and exit request."""

        try:
            # hardcode low timeout since we just want stuff to exit when exiting
            shut_resp = self._json_rpc.call("shutdown", None, timeout=0.1)
            self._json_rpc.notify("exit", None)
        except (jsonrpc.JsonRpcReadTimeout) as exc:
            # server is probably already dead. Log and be happy.
            log.debug("Got exception when waiting for shutdown response. %s", exc)

        self._json_rpc.stop()

    def cancel(self, id):
        """Cancel request."""
        request = {
            "id": id,
        }
        self._json_rpc.notify("$cancelRequest", request)

    # Workspace requests
    # wo is short for workspace
    def wo_did_change_configuration(self, settings):
        """Send workspace did change configuration notification."""
        request = {
            "settings": settings,
        }
        self._json_rpc.notify("workspace/didChangeConfiguration", request)

    def wo_did_change_watched_files(self, changes):
        request = {
            "changes": changes,
        }
        self._json_rpc.notify("workspace/didChangeWatchedFiles", request)

    def wo_symbol(self, query):
        request = {"query": query}
        response = self._json_rpc.call("workspace/symbol", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response


    # TextDocument requests
    # td is short for TextDocument
    def td_did_open(self, uri, language_id, version, text):
        """Send textdocument/didOpen notification.

        Args:
        """
        request = {
            "textDocument": create_td_item(uri, language_id, version, text),
        }
        self._json_rpc.notify("textDocument/didOpen", request)

    def td_did_change(self, uri, version, text):
        """Send textdocument/didChange notification.

        Args:
        """
        request = {
            "textDocument": {"uri": uri, "version": version},
            "contentChanges": [{"text": text}],  # TODO: Add support for ranges...
        }
        self._json_rpc.notify("textDocument/didChange", request)

    def td_did_close(self, uri):
        request = {
            "textDocument": {"uri": uri},
        }
        self._json_rpc.notify("textDocument/didClose", request)

    def td_did_save(self, uri):
        request = {
            "textDocument": {"uri": uri},
        }
        self._json_rpc.notify("textDocument/didSave", request)

    def td_completion(self, uri, line, character):
        request = create_td_position(uri, line, character)
        response = self._json_rpc.call("textDocument/completion", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        completions = []
        orig_result = response["result"]
        if isinstance(orig_result, dict):
            result = orig_result["items"]
        else:
            result = orig_result
        for compl in result:
            completions.append(LspClient.Completion(
                compl["label"],
                compl.get("kind", None),
                compl.get("detail", None),
                compl.get("documentation", None),
                orig_result,))

        return completions

    def ci_resolve(self, label, **kwargs):
        """Accept kwargs as defined in LSP protocol CompletionItem."""
        request = {
            "label": label
        }
        request.update(kwargs)
        response = self._json_rpc.call("completionItem/resolve", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_hover(self, uri, line, character):
        request = create_td_position(uri, line, character)
        response = self._json_rpc.call("textDocument/hover", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_signature_help(self, uri, line, character):
        request = create_td_position(uri, line, character)
        response = self._json_rpc.call("textDocument/signatureHelp", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_document_highlight(self, uri, line, character):
        request = create_td_position(uri, line, character)
        response = self._json_rpc.call(
            "textDocument/documentHighlight", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_document_symbol(self, uri):
        request = {
            "textDocument": {"uri": uri},
        }
        response = self._json_rpc.call(
            "textDocument/documentSymbol", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        symbols = []
        for sym in response["result"]:
            symbols.append(LspClient.Symbol(
                sym["name"],
                sym["kind"],
                sym.get("containerName", None),
                sym["location"]["uri"],
                sym["location"]["range"]["start"]["line"],
                sym["location"]["range"]["end"]["line"],
                sym["location"]["range"]["start"]["character"],
                sym["location"]["range"]["end"]["character"],
                response))
        return symbols

    def td_formatting(self, uri, tab_size, insert_spaces):
        """textDocumet/formatting.

        Args:
            uri(str): Path to document.
            tabs_size(int):
            insert_spaces(bool):

        Returns:
            dict:
        """
        # TODO: Allow custom signatures...
        request = {
            "textDocument": {"uri": uri},
            "options": {"tabSize": tab_size, "insertSpaces": insert_spaces}
        }
        response = self._json_rpc.call("textDocument/formatting", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_range_formatting(self, uri, tab_size, insert_spaces,
                            start_line, end_line, start_char, end_char):
        """textDocument/rangeFormatting."""
        # TODO: Allow custom signatures...
        request = {
            "textDocument": {"uri": uri},
            "options": {"tabSize": tab_size, "insertSpaces": insert_spaces},
            "range": create_range(start_line, end_line, start_char, end_char)
        }
        response = self._json_rpc.call(
            "textDocument/rangeFormatting", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_on_type_formatting(self, uri, tab_size, insert_spaces, line, character, ch):
        """textDocument/onTypeFormatting.
        Args:
            ch: "Characters typed."
            character(int): columnt number
        """
        # TODO: Allow custom signatures...
        request = {
            "textDocument": {"uri": uri},
            "options": {"tabSize": tab_size, "insertSpaces": insert_spaces},
            "position": create_position(line, character),
            "ch": ch
        }
        response = self._json_rpc.call(
            "textDocument/onTypeFormatting", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_definition(self, uri, line, character):
        """Send textDocument/definition request.

        Returns:
            list(Location):
        """
        request = create_td_position(uri, line, character)
        response = self._json_rpc.call(
            "textDocument/definition", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        locations = LspClient._get_locations(response)
        return locations

    def td_references(self, uri, line, character, include_declaration):
        request = create_td_position(uri, line, character)
        request["context"] = {"includeDeclaration": include_declaration}
        response = self._json_rpc.call("textDocument/references", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        locations = LspClient._get_locations(response)
        return locations

    def td_code_action(self, uri, start_line, end_line, start_char, end_char, diagnostics=None):
        """
        Args:
            diagnostics(list): list of diagnostics dicts
        """
        if diagnostics is None:
            diagnotstics = []

        request = {
            "textDocumet": {"uri": uri},
            "range": create_range(start_line, end_line, start_char, end_char),
            "context": {"diagnostics": diagnostics},
        }
        response = self._json_rpc.call(
            "textDocument/codeAction", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_code_lens(self, uri):
        request = {
            "textDocument": {"uri": uri},
        }
        response = self._json_rpc.call(
            "textDocument/codeLens", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def code_lens_resolve(self, code_lens):
        # TODO: Implement this properly?
        request = code_lens
        response = self._json_rpc.call(
            "codeLens/resolve", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_document_link(self, uri):
        request = {
            "textDocument": {"uri": uri},
        }
        response = self._json_rpc.call(
            "textDocument/documentLink", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def document_link_resolve(self, document_link):
        # TODO: Implement this properly?
        request = document_link
        response = self._json_rpc.call(
            "documentLink/resolve", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    def td_rename(self, uri, line, character, new_name):
        request = {
            "textDocument": {"uri": uri},
            "position": create_position(line, character),
            "newName": new_name
        }
        response = self._json_rpc.call(
            "textDocument/rename", request, timeout=self.timeout)
        LspClient._raise_on_error(response)
        return response

    @staticmethod
    def _raise_on_error(response):
        if "error" in response:
            err = response["error"]
            # Message and code should always be present
            raise LspError(err["message"], err["code"], err.get("data", None))

    @staticmethod
    def _get_locations(response):
        locations = []
        # Handle the fact that the respons can be either a list or a single Location
        orig_result = response["result"]
        if isinstance(orig_result, dict):
            result = [orig_result]
        else:
            result = orig_result
        for location in result:
            locations.append(
                LspClient.Location(location["uri"],
                location["range"]["start"]["line"],
                location["range"]["end"]["line"],
                location["range"]["start"]["character"],
                location["range"]["end"]["character"],
                response))
        return locations

# convinience funcitons
def create_td_item(uri, language_id, version, text):
    return {
        "uri": uri,
        "languageId": language_id,
        "version": version,
        "text": text
    }


def create_td_position(uri, line, character):
    return {
        # For LSP v1.0 compat inline uri
        "uri": uri,
        "textDocument": {"uri": uri},
        "position": create_position(line, character)
    }


def create_position(line, character):
    return {
        "line": line,
        "character": character,
    }


def create_range(start_line, end_line, start_char, end_char):
    return {
        "start": create_position(start_line, start_char),
        "end": create_position(end_line, end_char)
    }
