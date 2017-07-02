import json
import logging
import os

import vim

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# Vim commands
def current_file():
    return vim.current.buffer.name


def current_source():
    return "\n".join(vim.current.buffer)


def filetype():
    return vim.eval("&filetype")


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
    # use -5 to account for some overhead and the added ..
    max_width = int(vim.eval("&columns")) - 5
    trunc = (msg[:max_width] + "..") if len(msg) > max_width else msg

    # Disable showcmd which for some reason triggers the "ENTER prompt"
    old_showcmd = vim.eval("&showcmd")
    vim.command("set noshowcmd")
    vim.command("echohl WarningMsg | echo '{}' | echohl None".format(vimstr(trunc.strip())))
    vim.command("let &showcmd = {}".format(old_showcmd))


def clear_quickfix():
    vim.eval("setqflist([], 'r')")


def clear_signs(filename):
    vim.command("sign unplace * file={}".format(filename))


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


def display_quickfix(qf_content):
    # Vim list/dict just so happen to map to a json string
    cmd = "setqflist({})".format(json.dumps(qf_content, separators=(",", ":")))
    log.debug(cmd)
    vim.eval(cmd)
    # TODO: To not hard code height of quickfix window
    vim.command("rightbelow copen 5")
