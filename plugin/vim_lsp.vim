" Copyright 2017 Kristopher Heijari
"
" This file is part of vim-lsp.
"
" vim-lsp is free software: you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation, either version 3 of the License, or
" (at your option) any later version.
"
" vim-lsp is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with vim-lsp.  If not, see <http://www.gnu.org/licenses/>.
if !has("python")
    finish
endif

if exists("g:loaded_vim_lsp") || &cp
    finish
endif
" --------------------------------
"  Settings
" --------------------------------
let g:loaded_vim_lsp = 1
let g:vim_lsp_logdir = expand("<sfile>:h")."/log/"
let g:vim_lsp_log_to_file = 1
let g:vim_lsp_debug = 1

sign define LspSign text=>>

" --------------------------------
" Add our plugin to the path
" --------------------------------
python import os
python import sys
python import vim
python sys.path.append(vim.eval('expand("<sfile>:h")'))
python sys.path.append(os.path.join(vim.eval('expand("<sfile>:h")'), "vendor/lsp_client_py"))
python from vim_lsp import LSP

" --------------------------------
"  Function(s)
" --------------------------------
function! TdDidOpen()
python << endOfPython
LSP.td_did_open()
endOfPython
endfunction


function! TdDidClose()
python << endOfPython
LSP.td_did_close()
endOfPython
endfunction


function! TdDefinition()
python << endOfPython
LSP.td_definition()
endOfPython
endfunction


function! TdReferences()
python << endOfPython
LSP.td_references()
endOfPython
endfunction


function! TdSymbols()
python << endOfPython
LSP.td_symbols()
endOfPython
endfunction


function! LspClose()
python << endOfPython
LSP.shutdown_all()
endOfPython
endfunction


function! LspInsertLeave()
python << endOfPython
LSP.td_did_change()
LSP.process_diagnostics()
endOfPython
endfunction


function! LspCursorHold()
python << endOfPython
LSP.process_diagnostics()
endOfPython
endfunction


function! LspBufWritePost()
python << endOfPython
LSP.td_did_change()
LSP.td_did_save()
endOfPython
endfunction

function! TdDiagnostics()
python << endOfPython
LSP.display_diagnostics()
endOfPython
endfunction


function! LspCursorMoved()
python << endOfPython
LSP.display_sign_help()
endOfPython
endfunction
" --------------------------------
"  Omnifunc
" --------------------------------
function! LspOmniFunc(findstart, base)
python << endOfPython
LSP.td_completion()
endOfPython
endfunction

" --------------------------------
"  Expose our commands to the user
" --------------------------------
command! LspReferences call TdReferences()
command! LspDefinition call TdDefinition()
command! LspSymbols call TdSymbols()
command! LspDiagnostics call TdDiagnostics()

" --------------------------------
"  Register envents
" --------------------------------
augroup vim_lsp
    au BufNewFile,BufRead * call TdDidOpen()
    au BufDelete * call TdDidClose()
    au InsertLeave * call LspInsertLeave()
    au BufWritePost,FileWritePost * call LspBufWritePost()
    au VimLeavePre * call LspClose()
    au CursorHold * call LspCursorHold()
    au CursorMoved,CursorMovedI * call LspCursorMoved()
    " close preview window if visible
    au InsertLeave * if pumvisible() == 0|pclose|endif
augroup END

" --------------------------------
"  Key mappings
" --------------------------------
function! OmniComplete()
    if !empty(&omnifunc)
        return ".\<C-X>\<C-O>"
    else
        return "."
    endif
endfunction
inoremap <expr> . OmniComplete()
