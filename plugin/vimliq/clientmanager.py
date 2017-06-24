# Copyright 2017 Kristopher Heijari
#
# This file is part of vim-lsp.
#
# vim-lsp.is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vim-lsp.is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-lsp.  If not, see <http://www.gnu.org/licenses/>.

"""Client manager handling many vimlspclients."""

from functools import wraps
import logging
import os

import pylspc.client
import pylspc.jsonrpc

from . import client
from . import vimutils as V

import vim

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def handle_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except pylspc.client.LspError as exc:
            log.debug("Got error from LSP server. message=%s, code=%s, data=%s",
                      exc, exc.code, exc.data)
        except Exception:
            log.exception()

    return wrapper


class ClientManager(object):
    """Class managing all clients."""

    def __init__(self, supported_clients):
        """Initialize object.

        Args:
            supported_clients(dict): See supported_clients.json

        Attributes:
            clients(dict): Dict where key is the language and value is the client object.
        """
        self._supported_clients = supported_clients
        self.clients = {}

    def lang_supported(self):
        ft = V.filetype()
        if ft in self._supported_clients:
            return True
        return False

    def add_client(self):
        """Add a client."""
        ft = V.filetype()
        # Only add if supported and not already added
        if ft in self._supported_clients and ft not in self.clients:
            start_cmd = [self._supported_clients[ft]["start_cmd"]]
            transport = self._supported_clients[ft]["transport"]
            log_arg = self._supported_clients[ft].get("log_arg", None)

            if vim.eval("g:vim_lsp_log_to_file") == "1" and log_arg:
                start_cmd.append(log_arg)
                pid = os.getpid()
                start_cmd.append(os.path.join(vim.eval("g:vim_lsp_logdir"),
                                              "{}_lsp_server_{}.log".format(ft, pid)))

            l_client = client.VimLspClient(start_cmd, transport)
            l_client.start_server()
            self.clients[ft] = l_client

    def shutdown_all(self):
        """Called when vim closes."""
        for _, l_client in self.clients.items():
            l_client.shutdown()

    def __getattr__(self, name):
        """Forward function call to the correct lsp client."""
        filetype = V.filetype()
        try:
            client_ = self.clients[filetype]
        except KeyError:
            raise AttributeError("filetype: {}, name: {}".format(filetype, name))

        func = getattr(client_, name)
        return handle_error(func)
