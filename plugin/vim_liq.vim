" Copyright 2017 Kristopher Heijari
"
" This file is part of vim-liq.
"
" vim-liq is free software: you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation, either version 3 of the License, or
" (at your option) any later version.
"
" vim-liq is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with vim-liq.  If not, see <http://www.gnu.org/licenses/>.
if !has("python") && !has("python3")
    finish
elseif !has("timers")
    finish
endif


if exists("g:loaded_vim_lsp") || &cp
    finish
endif


" --------------------------------
"  Settings
" --------------------------------
if !exists("g:langIQ_servers")
    let g:langIQ_servers = {}
endif
if !exists("g:langIQ_disablekeymap")
    let g:langIQ_disablekeymap = 0
endif
if !exists("g:langIQ_disablesigns")
    let g:langIQ_disablesigns = 1
endif
if !exists("g:langIQ_disablehighlight")
    let g:langIQ_disablehighlight = 0
endif
let g:vim_lsp_logdir = expand("<sfile>:h")."/log/"
let g:vim_lsp_log_to_file = 0
let g:vim_lsp_debug = 1

let g:completor_python_omni_trigger = '\w{3,}$|
                                      \[\w\)\]\}\''\"]+\.\w*$|
                                      \^\s*from\s+[\w\.]*(?:\s+import\s+(?:\w*(?:,\s*)?)*)?|
                                      \^\s*import\s+(?:[\w\.]*(?:,\s*)?)*'
sign define LspSign text=>>

" --------------------------------
" Add our plugin to the path
" --------------------------------
python << endOfPython
import os
import sys
import vim
sys.path.append(vim.eval('expand("<sfile>:h")'))
sys.path.append(os.path.join(vim.eval('expand("<sfile>:h")'), "vendor/lsp"))
from vim_liq import LSP
lspLoaded = 0
if LSP:
    lspLoaded = 1
vim.command("let lspLoaded={}".format(lspLoaded))
from vim_liq import LSP_LOG
endOfPython

if lspLoaded == 0
    finish
endif

" If we get here the plugin should have loaded correctly
let g:loaded_vim_lsp = 1

" --------------------------------
"  Function(s)
" --------------------------------
function! TdDefinition()
python << endOfPython
LSP.definition()
endOfPython
endfunction


function! TdReferences()
python << endOfPython
LSP.references()
endOfPython
endfunction


function! TdSymbols()
python << endOfPython
LSP.symbols()
endOfPython
endfunction


function! TdDiagnostics()
python << endOfPython
LSP.display_diagnostics()
endOfPython
endfunction


function! LspProcess(id)
    if LangSupport()
        py LSP.process()
    endif
endfunction

function! LspFileType()
if LangSupport()
python << endOfPython
LSP.add_client()
endOfPython
endif

" TODO: Handle the support check better
" check again if there is support since the add_client might have failed
if LangSupport()
                " Start vim timer for processing messages
    call timer_start(100, 'LspProcess', {'repeat': -1})

    setlocal completeopt=longest,menuone,preview
    setlocal omnifunc=LspOmniFunc

    call RegisterCommand()
    call RegisterAutoCmd()
    if g:langIQ_disablekeymap == 0
        call RegisterKeyMap()
    endif
    py LSP.td_did_open()
endif

endfunction

function! RegisterAutoCmd()
    augroup vim_lsp
        au TextChanged,InsertLeave <buffer> py LSP.td_did_change()
        au BufUnload,VimLeavePre <buffer> py LSP.td_did_close()
        au BufWritePost,FileWritePost <buffer> py LSP.td_did_save()
        au BufEnter <buffer> py LSP.update_highlight()
        au CursorMoved,CursorMovedI <buffer> py LSP.display_diagnostics_help()
        " close preview window if visible
        au InsertLeave <buffer> if pumvisible() == 0|pclose|endif
    augroup END
endfunction


function! LangSupport()
python << endOfPython
import vim
vim.command("let langsupport = '{0}'".format(LSP.lang_supported()))
endOfPython
    if langsupport == "True"
        return 1
    end
    return 0
endfunction

function! LspOmniFunc(findstart, base)
    py LSP.omni_func()
endfunction


function! PrintLog()
python << endOfPython
vim.command("echo '{}'".format(LSP_LOG.get_logs()))
endOfPython
endfunction

" --------------------------------
"  Register envents
" --------------------------------
au FileType * call LspFileType()

" --------------------------------
"  Expose our commands to the user
" --------------------------------
function! RegisterCommand()
    command! LspReferences call TdReferences()
    command! LspDefinition call TdDefinition()
    command! LspSymbols call TdSymbols()
    command! LspDiagnostics call TdDiagnostics()
endfunction

command! LspLog call PrintLog()


function! RegisterKeyMap()
    " inoremap <silent> <buffer> . .<C-x><C-o>
    imap <buffer> <Nul> <C-Space>
    smap <buffer> <Nul> <C-Space>
    inoremap <silent> <buffer> <C-Space> <C-x><C-o>
    nnoremap <silent> <buffer> <leader>d :call TdDefinition()<CR>
    nnoremap <silent> <buffer> <leader>f :call TdReferences()<CR>
endfunction
