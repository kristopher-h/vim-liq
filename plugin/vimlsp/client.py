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
"""LSP client module."""
from functools import wraps
import json
import linecache
import logging
import os
import re

import pylspc.jsonrpc
import pylspc.client
import vim

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Vim commands
def current_file():
    return vim.current.buffer.name


def afile():
    return vim.eval("expand('<afile>')")


def current_source():
    return "\n".join(vim.current.buffer)


def filetype():
    return vim.eval("&filetype")


def root_path():
    return os.getcwd()


def cursor():
    """Return row, col zero based."""
    row, col = vim.current.window.cursor
    log.debug("cursor: %s, %s", row, col)
    # Account for the fact that vim is 1 based for lines while lsp proto is 0 based
    return (row - 1, col)


def vim_command(cmd):
    """Run cmd and return output."""
    vim.command("redir => lsp_cmd_var")
    vim.command("silent {}".format(cmd))
    vim.command("redir END")
    return vim.eval("lsp_cmd_var")


def jump_to(path, row, col):
    # row, col zero based
    vim.command("e {}".format(path))
    vim.current.window.cursor = (row + 1, col)


def vimstr(string):
    """Return escaped string.

    Args:
        string(str): a string
    """
    return string.replace("'", "''")


def warning(msg):
    vim.command("echohl WarningMsg | echo '{}' | echohl None".format(vimstr(msg)))


def display_quickfixlist(locations):
    """display quickfix list.

    Args:
        locations(list(Location)):
    """
    qf_content = []
    for loc in locations:
        qf_line = {"filename": loc.uri,
                   "lnum": loc.start_line + 1,
                   "col": loc.start_char,
                   "text": linecache.getline(loc.uri, loc.start_line + 1)}
        qf_content.append(qf_line)
        disp_qf_from_dict(qf_content)


def disp_qf_from_diag(filename, diagnostics):
    qf_content = []
    for loc in diagnostics:
        qf_line = {"filename": filename,
                   "lnum": loc.start_line + 1,
                   "col": loc.start_char,
                   "text": loc.message}
        qf_content.append(qf_line)
        disp_qf_from_dict(qf_content)


def disp_qf_from_dict(qf_content):
    # Vim list/dict just so happen to map to a json string
    cmd = "setqflist({})".format(json.dumps(qf_content, separators=(",", ":")))
    log.debug(cmd)
    vim.eval(cmd)
    # TODO: To not hard code height of quickfix window
    vim.command("rightbelow copen 5")


def clear_qf_list():
    vim.eval("setqflist([], 'r')")


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
    row, col = cursor()
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


def display_preview(text):
    # Function is unused but kept for future use
    prev_window = vim.eval("win_getid()")
    # Create new window
    # TODO: do not hardcode height
    vim.command("noautocmd 5new")
    # Set options
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal bufhidden=delete")
    vim.command("setlocal noswapfile")
    new_buf = vim.current.buffer
    if new_buf:
        # Buffer not empty something has gone wrong
        log.debug("Newly created buffer not empty. %s", new_buf)
    else:
        new_buf = text.split("\n")
    vim.eval("win_gotoid({})".format(prev_window))


def log_to_file():
    return vim.eval("g:vim_lsp_log_to_file") == "1"


def clear_signs(filename):
    vim.command("sign unplace * file={}".format(filename))


def _handle_lsp_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except pylspc.client.LspError as exc:
            log.debug("Got error from LSP server. message=%s, code=%s, data=%s",
                      exc, exc.code, exc.data)
        except VimLspError as exc:
            log.debug("Got error from vim-lsp. message=%s", exc)

    return wrapper


class VimLspError(Exception):
    """Raised on error from this module."""


class VimLspClient():
    """Vim Language Server Protocol client.

    VimLspClient also expose functions for communicating with the server.
    """

    def __init__(self, supported_clients):
        """Initialize

        Args:
            supported_clients(dict): See supported_clients.json
        """
        self._supported_clients = supported_clients
        self.clients = {}  # dict(<language>, Client)
        self.td_version = 0
        self._sign_id = 1
        self.diagnostics = {}

    def lang_supported(self):
        ft = filetype()
        if ft in self._supported_clients:
            return True
        return False

    def shutdown(self):
        lsp = self._client()
        lsp.shutdown()

    def shutdown_all(self):
        """Called when vim closes."""
        for _, client in self.clients.items():
            client.shutdown()

    def _client(self):
        """Return the correct client based on filetype.

        Create and start if not already done.

        Returns:
            LspClient:
        """
        ft = filetype()
        if ft not in self.clients:
            start_cmd = [self._supported_clients[ft]["start_cmd"]]
            transport = self._supported_clients[ft]["transport"]
            if transport == "STDIO":
                rpc_class = pylspc.jsonrpc.JsonRpcStdInOut
            else:
                raise VimLspError("Unknown transport protocol: {}".format(transport))
            if log_to_file() and self._supported_clients[ft].get("log_arg", None):
                start_cmd.append(self._supported_clients[ft]["log_arg"])
                pid = os.getpid()
                start_cmd.append(os.path.join(vim.eval("g:vim_lsp_logdir"),
                                              "{}_lsp_server_{}.log".format(ft, pid)))

            client = pylspc.client.LspClient(start_cmd, rpc_class=rpc_class)
            path = root_path()
            # TODO: What happens if init fails?
            client.initialize(root_path=path, root_uri=path)
            self.clients[ft] = client
        return self.clients[ft]

    def _next_sign_id(self):
        self._sign_id += 1
        file_ = current_file()
        all_ids = set(re.findall("id=(\d+)", vim_command("sign place file={}".format(file_))))
        while self._sign_id in all_ids:
            # cap at an arbitrary figure just for the sake of it
            if self._sign_id > 65000:
                self._sign_id = 1
            self._sign_id += 1

        return self._sign_id

    def update_signs(self):
        """Update signs in current buffer."""
        file_ = current_file()
        log.debug("Update signs for %s", file_)
        for diag in self.diagnostics.get(file_, []):
            id_ = self._next_sign_id()
            vim.command("sign place {id} line={line} name=LspSign "
                        "file={file}".format(id=id_, line=diag.start_line + 1, file=file_))

    def display_sign_help(self):
        filename = current_file()
        if filename in self.diagnostics:
            line, _ = cursor()
            # TODO: Improve performance here by indexing on line number as well as filename
            for diag in self.diagnostics[filename]:
                if diag.start_line == line:
                    warning("LspDiagnostic: {} | col: {} | {}:{}".format(
                        diag.message, diag.start_char, diag.source, diag.code))
                    break
            else:
                # clear
                warning("")

    def clear_signs(self):
        filename = current_file()
        clear_signs(filename)
        if filename in self.diagnostics:
            del self.diagnostics[filename]

    def process_diagnostics(self):
        log.debug("enter")
        cur_file = current_file()
        for _, lsp in self.clients.items():
            for diag in lsp.diagnostics():
                self.diagnostics[diag.uri] = diag.diagnostics
                if diag.uri == cur_file:
                    self.update_signs()

    def display_diagnostics(self):
        file_ = current_file()
        if file_ in self.diagnostics:
            diags = self.diagnostics[file_]
            disp_qf_from_diag(file_, diags)

    def td_did_open(self):
        lsp = self._client()
        language = filetype()
        self.td_version += 1
        lsp.td_did_open(current_file(), language, self.td_version, current_source())

    def td_did_change(self):
        self.clear_signs()
        lsp = self._client()
        self.td_version += 1
        lsp.td_did_change(current_file(), self.td_version, current_source())

    def td_did_save(self):
        self.clear_signs()
        lsp = self._client()
        lsp.td_did_save(current_file())
        self.process_diagnostics()

    def td_did_close(self):
        # Not using current file here since it might be the wrong name
        # when autocmd BufDelete is triggered.
        filepath = afile()
        # If filepath is empty there is no point in doing anything.
        # This can happen for example if closing quickfixlist buffer with cclose
        # while standing in an acutal buffer.
        if filepath:
            log.debug("Closing %s", filepath)
            lsp = self._client()
            lsp.td_did_close(current_file())

    @_handle_lsp_error
    def td_definition(self):
        lsp = self._client()
        row, col = cursor()
        definitions = lsp.td_definition(current_file(), row, col)
        if not definitions:
            warning("No definitions found")
        elif len(definitions) == 1:
            def_ = definitions[0]
            jump_to(def_.uri, def_.start_line, def_.start_char)
        else:
            # multiple matches
            display_quickfixlist(definitions)

    @_handle_lsp_error
    def td_references(self):
        lsp = self._client()
        row, col = cursor()
        references = lsp.td_references(current_file(), row, col, True)
        if not references:
            warning("No references found")
        elif len(references) == 1:
            ref = references[0]
            jump_to(ref.uri, ref.start_line, ref.start_char)
        else:
            # multiple matches
            display_quickfixlist(references)

    @_handle_lsp_error
    def td_symbols(self):
        lsp = self._client()
        symbols = lsp.td_document_symbol(current_file())
        if not symbols:
            warning("No symbolss found")
        # TODO: Improve symbol list to not only show locations
        display_quickfixlist(symbols)

    @_handle_lsp_error
    def td_completion(self):
        if omni_findstart():
            return
        # Make sure server has latest info before trying to complete
        # Since life is tough we have to do some wierd things
        base, source = omni_add_base()
        lsp = self._client()
        self.td_version += 1
        lsp.td_did_change(current_file(), self.td_version, source)
        row, col = cursor()
        completions = lsp.td_completion(current_file(), row, col + len(base))
        # End of though love
        display_completions(completions)

    def stop(self):
        """Stop vim_lsp_client server."""
        lsp = self._client()
        lsp.shutdown()

