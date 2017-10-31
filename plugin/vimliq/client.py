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
import json
import linecache
import logging
import os
import re
import time

import lsp.client
import lsp.jsonrpc

from . import vimutils as V

import vim

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# Vim commands
# TODO: move to private in VimLspClient or make generic in vimutils
def omni_findstart():
    """Check if this is the first invocation of omnifunc.

    Call vim legacy stuff for this.
    """
    if vim.eval("a:findstart") == "1":
        vim.command("return syntaxcomplete#Complete(1, '')")
        return True
    return False


def omni_add_base():
    base = vim.eval("a:base")
    row, col = V.cursor()
    # source = copy.deepcopy(vim.current.buffer)
    source = vim.current.buffer[:]
    line = source[row]
    source[row] = line[:col] + base + line[col:]
    return (base, "\n".join(source))


def display_completions(completions):
    """display completions list.

    Since this is invoked by omnifunc vim is expecting to get a list with completions
    returned.

    Args:
        completions(list(Completion)):

    """
    content = []
    for comp in completions:
        comp_line = {"word": comp.label}
        if comp.kind:
            kind = ""
            if comp.kind in [1, 2]:
                kind = "f"
            elif comp.kind in [5, 10]:
                kind = "m"
            elif comp.kind in [6]:
                kind = "v"
            if kind:
                comp_line["kind"] = kind

        if comp.detail:
            comp_line["menu"] = comp.detail

        if comp.documentation:
            comp_line["info"] = comp.documentation

        content.append(comp_line)

    # Vim list/dict just so happen to map to a json string
    retstr = json.dumps(content, separators=(",", ":"))
    vim.command("return {}".format(retstr))


class VimLspError(Exception):
    """Raised on error from this module."""


class VimLspClient(object):
    """Vim Language Server Protocol client.

    VimLspClient also expose functions for communicating with the server.
    """

    def __init__(self, start_cmd, transport, use_signs=True):
        """Initialize

        Args:
            start_cmd(str): Command used to start LSP server connected to this client.
            transport(str): Currently only "STDIO" is supported.
            use_signs(bool): If True use vim "signs".
        """
        self._start_cmd = start_cmd
        self._transport = transport
        self._use_signs = use_signs
        self.td_version = 0
        self._sign_id = 1
        self.diagnostics = {}
        self._client = None

    def shutdown(self):
        self._client.shutdown()

    def start_server(self):
        """Start the LSP client and the server."""
        if self._transport == "STDIO":
            rpc_class = lsp.jsonrpc.JsonRpcStdInOut
        else:
            raise VimLspError("Unknown transport protocol: {}".format(self._transport))

        self._client = lsp.client.LspClient(self._start_cmd, rpc_class=rpc_class)
        path = os.getcwd()
        # TODO: What happens if init fails?
        self._client.initialize(root_path=path, root_uri="file://" + path)

    def _next_sign_id(self):
        log.debug("next sign %s", time.time())
        self._sign_id += 1
        file_ = V.current_file()
        all_ids = set(re.findall("id=(\d+)", V.vim_command("sign place file={}".format(file_))))
        while self._sign_id in all_ids:
            # cap at an arbitrary figure just for the sake of it
            if self._sign_id > 65000:
                self._sign_id = 1
            self._sign_id += 1

        log.debug("next sign %s", time.time())
        return self._sign_id

    @staticmethod
    def _parse_uri(uri):
        """Parse uri."""
        return re.sub("file://", "", uri)

    def update_signs(self):
        """Update signs in current buffer."""
        file_ = V.current_file()
        log.debug("Update signs for %s", file_)
        self.clear_signs()
        for diag in self.diagnostics.get(file_, []):
            id_ = self._next_sign_id()
            vim.command("sign place {id} line={line} name=LspSign "
                        "file={file}".format(id=id_, line=diag.start_line + 1, file=file_))

    def display_sign_help(self):
        filename = V.current_file()
        if filename in self.diagnostics:
            line, _ = V.cursor()
            # TODO: Improve performance here by indexing on line number as well as filename
            for diag in self.diagnostics[filename]:
                if diag.start_line == line:
                    V.warning("LspDiagnostic: {} | col: {} | {}:{}".format(
                        diag.message, diag.start_char, diag.source, diag.code))
                    break
            else:
                # clear
                V.warning("")

    def clear_signs(self):
        filename = V.current_file()
        V.clear_signs(filename)

    def process_diagnostics(self):
        cur_file = V.current_file()
        for diag in self._client.diagnostics():
            local_uri = self._parse_uri(diag.uri)
            self.diagnostics[local_uri] = diag.diagnostics
            if local_uri == cur_file and self._use_signs:
                self.update_signs()

    def display_diagnostics(self):
        file_ = V.current_file()
        if file_ in self.diagnostics:
            diags = self.diagnostics[file_]
            self._display_quickfix_from_diagnostics(file_, diags)

    def td_did_open(self):
        language = V.filetype()
        self.td_version += 1
        self._client.td_did_open(
            "file://" + V.current_file(), language, self.td_version, V.current_source())

    def td_did_change(self):
        self.td_version += 1
        self._client.td_did_change(
            "file://" + V.current_file(), self.td_version, V.current_source())

    def td_did_save(self):
        self._client.td_did_save("file://" + V.current_file())
        self.process_diagnostics()

    def td_did_close(self):
        # Not using current file here since it might be the wrong name
        # when autocmd BufDelete is triggered.
        filepath = vim.eval("expand('<afile>')")
        # If filepath is empty there is no point in doing anything.
        # This can happen for example if closing quickfixlist buffer with cclose
        # while standing in an acutal buffer.
        if filepath:
            log.debug("Closing %s", filepath)

            self._client.td_did_close(filepath)

    def td_definition(self):
        row, col = V.cursor()
        definitions = self._client.td_definition("file://" + V.current_file(), row, col)
        if not definitions:
            V.warning("No definitions found")
        elif len(definitions) == 1:
            def_ = definitions[0]
            V.jump_to(self._parse_uri(def_.uri), def_.start_line, def_.start_char)
        else:
            # multiple matches
            self._display_quickfix_from_location(definitions)

    def td_references(self):
        row, col = V.cursor()
        references = self._client.td_references("file://" + V.current_file(), row, col, True)
        if not references:
            V.warning("No references found")
        elif len(references) == 1:
            ref = references[0]
            V.jump_to(self._parse_uri(ref.uri), ref.start_line, ref.start_char)
        else:
            # multiple matches
            self._display_quickfix_from_location(references)

    def td_symbols(self):
        symbols = self._client.td_document_symbol("file://" + V.current_file())
        if not symbols:
            V.warning("No symbols found")
        # TODO: Improve symbol list to not only show locations
        self._display_quickfix_from_location(symbols)

    def td_completion(self):
        if omni_findstart():
            return
        # Make sure server has latest info before trying to complete
        # Since life is tough we have to do some wierd things
        base, source = omni_add_base()

        self.td_version += 1
        self._client.td_did_change("file://" + V.current_file(), self.td_version, source)
        row, col = V.cursor()
        completions = self._client.td_completion("file://" + V.current_file(), row, col + len(base))
        # End of though love
        display_completions(completions)

    @staticmethod
    def _display_quickfix_from_location(locations):
        """display quickfix list.

        Args:
            locations(list(Location)):
        """
        qf_content = []
        for loc in locations:
            uri = VimLspClient._parse_uri(loc.uri)
            qf_line = {"filename": uri,
                       "lnum": loc.start_line + 1,
                       "col": loc.start_char,
                       "text": linecache.getline(uri, loc.start_line + 1)}
            qf_content.append(qf_line)
        V.display_quickfix(qf_content)

    @staticmethod
    def _display_quickfix_from_diagnostics(filename, diagnostics):
        qf_content = []
        for loc in diagnostics:
            qf_line = {"filename": filename,
                       "lnum": loc.start_line + 1,
                       "col": loc.start_char,
                       "text": loc.message}
            qf_content.append(qf_line)
        V.display_quickfix(qf_content)
