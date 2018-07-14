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
"""Language server protocol definitions.

This module contains definitions for the various objects in a LSP dict. In essensce
the only thing added by this module is the convenience of having all keynames predefined.
"""

# TD = Text Document
# K = Key
# M = Method

# JSON RPC keys
K_ID = "id"
K_PARAMS = "params"
K_METHOD = "method"
K_ERROR = "error"
K_RESULT = "result"

# Methods
M_INITIALIZE = "initialize"
M_INITIALIZED = "initialized"
M_TD_DID_OPEN = "textDocument/didOpen"
M_TD_DID_SAVE = "textDocument/didSave"
M_TD_DID_CHANGE = "textDocument/didChange"
M_TD_DID_CLOSE = "textDocument/didClose"
M_DIAGNOSTICS = "textDocument/publishDiagnostics"
M_TD_COMPLETION = "textDocument/completion"
M_TD_REFERENCES = "textDocument/references"
M_TD_DEFINITION = "textDocument/definition"
M_TD_SYMBOLS = "textDocument/documentSymbol"

# LSP Keys
K_PROCESS_ID = "processId"
K_ROOT_PATH = "rootPath"
K_ROOT_URI = "rootUri"
K_CAPABILITES = "capabilities"

K_TD = "textDocument"
K_CONTENT_CHANGES = "contentChanges"
K_URI = "uri"
K_LANG_ID = "languageId"
K_VERSION = "version"
K_TEXT = "text"
K_DIAGNOSTICS = "diagnostics"
K_RANGE = "range"
K_START = "start"
K_END = "end"
K_LINE = "line"
K_CHAR = "character"
K_MESSAGE = "message"
K_SOURCE = "source"
K_CODE = "code"
K_POSITION = "position"
K_ITEMS = "items"
K_LABEL = "label"
K_DETAIL = "detail"
K_DOCUMENTATION = "documentation"
K_KIND = "kind"
K_LOCATION = "location"
K_NAME = "name"

K_CONTEXT = "context"
K_INCLUDE_DECLARATION = "includeDeclaration"
