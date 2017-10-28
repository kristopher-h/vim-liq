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
import collections
import json
import logging
import logging.handlers
import os

import vim

import vimliq.clientmanager
import vimliq.vimutils as V

plugin_dir = os.path.dirname(__file__)
server_file = os.path.join(plugin_dir, "servers.json")


# Custom memory logger
class MemHandler(logging.Handler):
    def __init__(self, capacity):
        """Initialize the handler with the buffer size.

        Attributes:
            buffer(collections.deque): the buffer

        """
        logging.Handler.__init__(self)
        self.buffer = collections.deque(maxlen=capacity)

    def emit(self, record):
        """Emit a record. Just append to buffer."""
        self.buffer.append(record)

    def flush(self):
        """No flush needed, deque handles that."""

    def get_logs(self):
        logs = []
        for record in self.buffer:
            logs.append(self.format(record))

        return V.vimstr("\n".join(logs))


LSP_LOG = MemHandler(1000)
LSP = None


# Setup logging
log = logging.getLogger()
if vim.eval("g:vim_lsp_debug") == "1":
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

if vim.eval("g:vim_lsp_log_to_file") == "1":
    pid = os.getpid()
    log_dir = vim.eval("g:vim_lsp_logdir")
    # Create dir if it does not exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "vim_lsp_{}.log".format(pid)),
        maxBytes=500000, backupCount=2)
else:
    handler = LSP_LOG

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

supported_clients = {}
if os.path.isfile(server_file):
    with open(server_file, "r") as indata:
        try:
            supported_clients = json.load(indata)
            user_servers = vim.eval("g:langIQ_servers")
            log.debug("User specified language servers: %s", user_servers)
            supported_clients.update(user_servers)

            # Make relative paths absolute
            for _, client in supported_clients.items():
                client["cmd"] = client["cmd"].replace("{{ PLUGIN_DIR }}", plugin_dir)
            LSP = vimliq.clientmanager.ClientManager(supported_clients)
        except ValueError:
            log.error("Failed to load json file.")
else:
    log.info("No supported clients file found. Forgot to install?")
