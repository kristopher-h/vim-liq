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

"""Client manager handling many vimlspclients."""

from functools import wraps
import logging
import shlex

import lsp.client
import lsp.jsonrpc

from . import client
from . import vimutils as V


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def handle_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except lsp.client.LspError as exc:
            log.debug("Got error from LSP server. message=%s, code=%s, data=%s",
                      exc, exc.code, exc.data)
        except Exception:
            log.exception("")

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
            start_cmd = shlex.split(self._supported_clients[ft]["cmd"])
            transport = self._supported_clients[ft]["transport"]

            log.debug("Starting client, start_cmd: %s, transport: %s", start_cmd, transport)
            try:
                l_client = client.VimLspClient(start_cmd, transport)
                l_client.start_server()
                log.debug("Added client for %s", ft)
                self.clients[ft] = l_client
            except (lsp.client.LspError, OSError, IOError) as exc:
                log.error("Failed to add client for %s. Got error %s", ft, exc)
                # remove client from supported to avoid further calls
                del self._supported_clients[ft]

    @handle_error
    def shutdown_all(self):
        """Called when vim closes."""
        for lang, l_client in self.clients.items():
            log.debug("Shutdown client for language, %s", lang)
            l_client.shutdown()

    def __getattr__(self, name):
        """Forward function call to the correct lsp client."""
        filetype = V.filetype()
        try:
            client_ = self.clients[filetype]
        except KeyError:
            raise AttributeError("filetype: {}, name: {}".format(filetype, name))

        attr = getattr(client_, name)

        # If function return with wrapper
        if callable(attr):
            return handle_error(attr)
        else:
            return attr
