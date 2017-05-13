import json
import logging
import logging.handlers
import os

import vim

import vimlsp.client

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
with open(os.path.join(os.path.dirname(__file__), "supported_clients.json"), "r") as indata:
    supported_clients = json.load(indata)

LSP = vimlsp.client.VimLspClient(supported_clients)
