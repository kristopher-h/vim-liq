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
import json
import logging
import logging.handlers
import os

import vim

import vimliq.clientmanager

# Setup logging
log = logging.getLogger()
if vim.eval("g:vim_lsp_debug") == "1":
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

if vim.eval("g:vim_lsp_log_to_file") == "1":
    pid = os.getpid()
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(vim.eval("g:vim_lsp_logdir"), "vim_lsp_{}.log".format(pid)),
        maxBytes=500000, backupCount=2)
else:
    handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

supported_clients = {}
with open(os.path.join(os.path.dirname(__file__), "supported_servers.json"), "r") as indata:
    supported_clients = json.load(indata)

LSP = vimliq.clientmanager.ClientManager(supported_clients)
