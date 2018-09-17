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
"""LSP client module."""
import functools
import json
import logging
import os
import re
import time
try:
    import Queue as queue
except ImportError:
    import queue

import vimliq.base as base
import vimliq.jsonrpc as jsonrpc
import vimliq.lsp as P
import vimliq.vimutils as V

import vim

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class VimLspError(Exception):
    """Raised on error from this module."""


class VimLspClient(object):
    """Vim Language Server Protocol client.

    VimLspClient also expose functions for communicating with the server.
    """

    def __init__(self, start_cmd):
        """Initialize

        Args:
            start_cmd(str): Command used to start LSP server connected to this client.
            use_signs(bool): If True use vim "signs".
        """
        self._start_cmd = start_cmd
        self._use_signs = vim.eval("g:langIQ_disablesigns") == "0"
        self._use_highlight = vim.eval("g:langIQ_disablehighlight") == "0"
        self.td_version = 0
        self._sign_id = 1
        self.diagnostics = {}
        self.completions = "[]"
        self.initialized = False
        self._proc_id = os.getpid()
        self.rpc = None
        self.io = None
        self._event_queue = queue.Queue()

    def shutdown(self):
        self.io.close()

    def process(self):
        while not self._event_queue.empty():
            handler, result, exception = self._event_queue.get()
            # For now just log the error
            if exception:
                log.warn("Server replied with an error. Error: %s", exception)
                return
            handler(result)

    def _handler(self, handler):
        return functools.partial(self.handle_msg, self, handler)

    def start_server(self):
        """Start the LSP client and the server."""
        self.io = base.StdIO(self._start_cmd)
        self.io.connect()
        transport = base.LspBase(self.io)
        self.rpc = jsonrpc.JsonRpc(transport)
        self.rpc.register_notification_handler(
            P.M_DIAGNOSTICS, self._handler(self.handle_diagnostics))
        self.initialize()

    # Request methods
    def initialize(self):
        params = {
            P.K_PROCESS_ID: self._proc_id,
            P.K_ROOT_URI: "file://" + os.getcwd(),
            P.K_CAPABILITES: {},
        }
        self.rpc.call_async(P.M_INITIALIZE, params, callback=self._handler(self.handle_initialize))

    def completion(self):
        if not self.initialized:
            return {}
        row, col = V.cursor()
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
            },
            P.K_POSITION: {
                P.K_LINE: row,
                P.K_CHAR: col,
            }
        }
        try:
            completions = self.rpc.call(P.M_TD_COMPLETION, params)
        except jsonrpc.JsonRpcError as exc:
            log.error("Completion failed. Error: %s", exc)
            completions = {}
        result = self._parse_completion(completions)
        return result

    # Notifications
    def initialized(self):
        """Send initialized message."""
        self.rpc.call_async(P.M_INITIALIZED, {}, notify=True)

    def references(self):
        if not self.initialized:
            return
        row, col = V.cursor()
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
            },
            P.K_POSITION: {
                P.K_LINE: row,
                P.K_CHAR: col,
            },
            P.K_CONTEXT: {
                P.K_INCLUDE_DECLARATION: True,
            },
        }
        self.rpc.call_async(
            P.M_TD_REFERENCES, params, callback=self._handler(self.handle_references))

    def definition(self):
        if not self.initialized:
            return
        row, col = V.cursor()
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
            },
            P.K_POSITION: {
                P.K_LINE: row,
                P.K_CHAR: col,
            },
            P.K_CONTEXT: {
                P.K_INCLUDE_DECLARATION: True,
            },
        }
        self.rpc.call_async(
            P.M_TD_DEFINITION, params, callback=self._handler(self.handle_definition))

    def symbols(self):
        if not self.initialized:
            return
        row, col = V.cursor()
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
            },
        }
        self.rpc.call_async(
            P.M_TD_SYMBOLS, params, callback=self._handler(self.handle_symbols))

    def td_did_open(self):
        if not self.initialized:
            return
        self.td_version += 1
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
                P.K_LANG_ID: V.filetype(),
                P.K_VERSION: self.td_version,
                P.K_TEXT: V.current_source()
            }
        }
        self.rpc.call_async(P.M_TD_DID_OPEN, params, notify=True)

    def td_did_save(self):
        if not self.initialized:
            return
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
            }
        }
        self.rpc.call_async(P.M_TD_DID_SAVE, params, notify=True)

    def td_did_close(self):
        if not self.initialized:
            return
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
            }
        }
        self.rpc.call_async(P.M_TD_DID_CLOSE, params, notify=True)

    def td_did_change(self):
        if not self.initialized:
            return
        self.td_version += 1
        params = {
            P.K_TD: {
                P.K_URI: "file://" + V.current_file(),
                P.K_VERSION: self.td_version,
            },
            P.K_CONTENT_CHANGES: [{
                P.K_TEXT: V.current_source(),
            }],
        }
        self.rpc.call_async(P.M_TD_DID_CHANGE, params, notify=True)

    # async handlers
    @staticmethod
    def handle_msg(self, handler, result, exception):
        self._event_queue.put((handler, result, exception))

    def handle_initialize(self, msg):
        """Handle initialize response."""
        log.debug("Initialized.")
        self.initialized = True
        # self.initialized()
        # TODO: Loop through all open files? And not only current?
        self.td_did_open()

    def handle_references(self, msg):
        """Handle references msg."""
        if not msg:
            V.warning("No references found")
            return
        qf_content = []
        for loc in msg:
            qf_line = {
                "filename": self._parse_uri(loc[P.K_URI]),
                "lnum": loc[P.K_RANGE][P.K_START][P.K_LINE] + 1,
                "col": loc[P.K_RANGE][P.K_START][P.K_CHAR],
            }
            qf_content.append(qf_line)
        V.display_quickfix(qf_content)

    def handle_definition(self, msg):
        """Handle definition msg."""
        log.debug(msg)
        if not msg:
            V.warning("No definition found")
            return
        qf_content = []
        for loc in msg:
            qf_line = {
                "filename": self._parse_uri(loc[P.K_URI]),
                "lnum": loc[P.K_RANGE][P.K_START][P.K_LINE],
                "col": loc[P.K_RANGE][P.K_START][P.K_CHAR],
            }
            qf_content.append(qf_line)

        if len(qf_content) == 1:
            jto = qf_content[0]
            V.jump_to(jto["filename"], jto["lnum"], jto["col"])
        else:
            V.display_quickfix(qf_content)

    def handle_symbols(self, msg):
        """Handle symbols response."""
        log.debug(msg)
        if not msg:
            V.warning("No symbols found")
            return
        qf_content = []
        for sym in msg:
            qf_line = {
                "filename": self._parse_uri(sym[P.K_LOCATION][P.K_URI]),
                "lnum": sym[P.K_LOCATION][P.K_RANGE][P.K_START][P.K_LINE],
                "col": sym[P.K_LOCATION][P.K_RANGE][P.K_START][P.K_CHAR],
                "text": sym[P.K_NAME],
            }
            qf_content.append(qf_line)

        V.display_quickfix(qf_content)

    def handle_diagnostics(self, msg):
        """Handle diagnostics notifications."""
        log.debug("enter")
        local_uri = self._parse_uri(msg[P.K_URI])
        self.diagnostics[local_uri] = msg[P.K_DIAGNOSTICS]
        if self._use_signs:
            self.update_signs(local_uri)
        if self._use_highlight:
            self.update_highlight(local_uri)

    # Public functions
    def display_diagnostics(self):
        filename = V.current_file()
        if filename not in self.diagnostics:
            return

        diagnostics = self.diagnostics[filename]
        qf_content = []
        for loc in diagnostics:
            qf_line = {"filename": filename,
                       "lnum": loc[P.K_RANGE][P.K_START][P.K_LINE] + 1,
                       "col": loc[P.K_RANGE][P.K_START][P.K_CHAR],
                       "text": loc[P.K_MESSAGE]}
            qf_content.append(qf_line)
        V.display_quickfix(qf_content)

    def display_diagnostics_help(self):
        filename = V.current_file()
        if filename in self.diagnostics:
            line, _ = V.cursor()
            # TODO: Improve performance here by indexing on line number as well as filename
            for diag in self.diagnostics[filename]:
                if diag[P.K_RANGE][P.K_START][P.K_LINE] == line:
                    V.warning("LspDiagnostic: {} | col: {} | {}:{}".format(
                        diag[P.K_MESSAGE],
                        diag[P.K_RANGE][P.K_START][P.K_CHAR],
                        diag.get(P.K_SOURCE, ""),
                        diag.get(P.K_CODE, "")
                    ))
                    break
            else:
                # clear
                V.warning("")

    def update_highlight(self, file_=None):
        if not file_:
            file_ = V.current_file()
        log.debug("Update highlight for %s", file_)

        try:
            vim.command("call matchdelete(w:langiq_match)")
        except vim.error:
            pass

        match_regex = []
        for diag in self.diagnostics.get(file_, []):
            line = diag[P.K_RANGE][P.K_START][P.K_LINE] + 1
            col_start = diag[P.K_RANGE][P.K_START][P.K_CHAR]
            if col_start < 0:
                col_start = 0
            col_end = diag[P.K_RANGE][P.K_END][P.K_CHAR] + 1
            if col_end < 0:
                col_end = 0
            match_regex.append(r"\%{}l\%1c".format(line))
            match_regex.append(r"\%{}l\%>{}v.\%<{}v".format(line, col_start, col_end))

        cmd = r"let w:langiq_match=matchadd('ColorColumn', '{}')".format(r"\|".join(match_regex))
        log.debug("Highlight cmd: %s", cmd)
        vim.command(cmd)

    def omni_func(self):
        """Blocking omnifunc."""
        if vim.eval("a:findstart") == "1":
            vim.command("return syntaxcomplete#Complete(1, '')")
            return
        self.td_did_change()
        completions = self.completion()
        vim.command("return {}".format(completions))

    def update_signs(self, file_=None):
        """Update signs in current buffer."""
        # If completion is ongoing to not show signs as it is insanely slow
        # and causes flickering.
        if not file_:
            file_ = V.current_file()
        log.debug("Update signs for %s", file_)
        self.clear_signs()
        for diag in self.diagnostics.get(file_, []):
            id_ = self._next_sign_id()
            vim.command(
                "sign place {id} line={line} name=LspSign file={file}".format(
                    id=id_,
                    line=diag[P.K_RANGE][P.K_START][P.K_LINE] + 1,
                    file=file_
                )
            )

    def clear_signs(self):
        filename = V.current_file()
        V.clear_signs(filename)

    # Private functions
    def _get_id(self):
        """Get unique request id."""
        self._id += 1
        return self._id

    def _next_sign_id(self):
        log.debug("next sign %s", time.time())
        self._sign_id += 1
        file_ = V.current_file()
        all_ids = set(re.findall(r"id=(\d+)", V.vim_command("sign place file={}".format(file_))))
        while self._sign_id in all_ids:
            # cap at an arbitrary figure just for the sake of it
            if self._sign_id > 65000:
                self._sign_id = 1
            self._sign_id += 1

        log.debug("next sign %s", time.time())
        return self._sign_id

    @staticmethod
    def _parse_completion(msg):
        """Parse completion response."""
        content = []
        for comp in msg.get(P.K_ITEMS, []):
            comp_line = {"word": comp[P.K_LABEL]}
            kind = comp.get(P.K_KIND)
            if kind:
                vimkind = ""
                if kind in [1, 2]:
                    vimkind = "f"
                elif kind in [5, 10]:
                    vimkind = "m"
                elif kind in [6]:
                    vimkind = "v"
                if vimkind:
                    comp_line["kind"] = vimkind

            detail = comp.get(P.K_DETAIL)
            if detail:
                comp_line["menu"] = detail

            doc = comp.get(P.K_DOCUMENTATION, "")
            if doc:
                comp_line["info"] = doc

            content.append(comp_line)

        # Vim list/dict just so happen to map to a json string
        return json.dumps(content, separators=(",", ":"))

    @staticmethod
    def _parse_uri(uri):
        """Parse uri."""
        return re.sub("file://", "", uri)
