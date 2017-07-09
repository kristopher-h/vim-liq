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
let g:vim_lsp_log_to_file = 0
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
python from vim_liq import LSP
python from vim_liq import LSP_LOG

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
LSP.process_diagnostics()
endOfPython
endfunction


function! LspFileType()
if LangSupport()
python << endOfPython
LSP.add_client()
endOfPython
    setlocal completeopt=longest,menuone,preview
    setlocal omnifunc=LspOmniFunc

    call RegisterCommand()
    call RegisterAutoCmd()
    call RegisterKeyMap()
    call TdDidOpen()
end
endfunction


function! RegisterAutoCmd()
    augroup vim_lsp
        au BufUnload <buffer> call TdDidClose()
        au InsertLeave <buffer> call LspInsertLeave()
        au BufWritePost,FileWritePost <buffer> call LspBufWritePost()
        au VimLeavePre <buffer> call LspClose()
        au CursorHold <buffer> call LspCursorHold()
        au CursorMoved,CursorMovedI <buffer> call LspCursorMoved()
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
python << endOfPython
LSP.td_completion()
endOfPython
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

" --------------------------------
"  Key mappings
" --------------------------------
function! LspIsComment()
    let m_col = col(".")
    let end_col = col("$")
    " If we are at end of line in insert mode we are out of 'scope'
    " If we are on the first col we are not
    if m_col >= end_col && m_col > 1
        let m_col = m_col - 1
    endif
    let highlight = synIDattr(synIDtrans(synID(line("."), m_col, 0)), "name")
    let syntaxtype = join(map(synstack(line('.'), m_col), 'synIDattr(v:val, "name")'))
    if highlight =~ 'Comment\|Constant\|PreProc'
        return 1
    elseif syntaxtype =~ 'Quote\|String\|Comment'
        return 1
    else
        return 0
    endif
endfunction


function! LspOmni(noselect)
    if LspIsComment()
        return ""
    elseif pumvisible() && !a:noselect
        return "\<C-n>"
    else
        return "\<C-x>\<C-o>\<C-r>=LspOmniOpened(" . a:noselect . ")\<CR>"
    endif
endfunction


function! LspOmniOpened(noselect)
    if !a:noselect && stridx(&completeopt, 'longest') > -1
        return "\<C-n>"
    endif
    return ""
endfunction

function! RegisterKeyMap()
    inoremap <expr> <buffer> . "." . LspOmni(1)
    imap <buffer> <Nul> <C-Space>
    " smap <buffer> <Nul> <C-Space>
    inoremap <silent> <buffer> <C-Space> <C-R>=LspOmni(0)<CR>
    " inoremap <expr> <buffer> <C-Space> <C-R>=LspOmni(0)<CR>
    nnoremap <silent> <buffer> <leader>d :call TdDefinition()<CR>
    nnoremap <silent> <buffer> <leader>f :call TdReferences()<CR>
endfunction
