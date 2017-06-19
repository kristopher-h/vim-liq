import json
import logging
import os

import vim

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# Vim commands
def current_file():
    return vim.current.buffer.name


def afile():
    return vim.eval("expand('<afile>')")


def current_source():
    return "\n".join(vim.current.buffer)


def filetype():
    return vim.eval("&filetype")


def root_path():
    return os.getcwd()


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
    vim.command("echohl WarningMsg | echo '{}' | echohl None".format(vimstr(msg)))


def display_quickfixlist(locations):
    """display quickfix list.

    Args:
        locations(list(Location)):
    """
    qf_content = []
    for loc in locations:
        qf_line = {"filename": loc.uri,
                   "lnum": loc.start_line + 1,
                   "col": loc.start_char,
                   "text": linecache.getline(loc.uri, loc.start_line + 1)}
        qf_content.append(qf_line)
        disp_qf_from_dict(qf_content)


def disp_qf_from_diag(filename, diagnostics):
    qf_content = []
    for loc in diagnostics:
        qf_line = {"filename": filename,
                   "lnum": loc.start_line + 1,
                   "col": loc.start_char,
                   "text": loc.message}
        qf_content.append(qf_line)
        disp_qf_from_dict(qf_content)


def disp_qf_from_dict(qf_content):
    # Vim list/dict just so happen to map to a json string
    cmd = "setqflist({})".format(json.dumps(qf_content, separators=(",", ":")))
    log.debug(cmd)
    vim.eval(cmd)
    # TODO: To not hard code height of quickfix window
    vim.command("rightbelow copen 5")


def clear_qf_list():
    vim.eval("setqflist([], 'r')")


def omni_findstart():
    """Check if this is the first invocation of omnifunc.

    Call vim legacy stuff for this.
    """
    if vim.eval("a:findstart") == "1":
        vim.command("return syntaxcomplete#Complete(1, '')")
        return True
    return False


def omni_add_base():
    base = vim.eval("a:base")
    row, col = cursor()
    # source = copy.deepcopy(vim.current.buffer)
    source = vim.current.buffer[:]
    line = source[row]
    source[row] = line[:col] + base + line[col:]
    return (base, "\n".join(source))


def display_completions(completions):
    """display completions list.

    Since this is invoked by omnifunc vim is expecting to get a list with completions
    returned.

    Args:
        completions(list(Completion)):

    """
    content = []
    for comp in completions:
        comp_line = {"word": comp.label}
        if comp.kind:
            kind = ""
            if comp.kind in [1, 2]:
                kind = "f"
            elif comp.kind in [5, 10]:
                kind = "m"
            elif comp.kind in [6]:
                kind = "v"
            if kind:
                comp_line["kind"] = kind

        if comp.detail:
            comp_line["menu"] = comp.detail

        comp_line["info"] = comp.documentation

        content.append(comp_line)

    # Vim list/dict just so happen to map to a json string
    retstr = json.dumps(content, separators=(",", ":"))
    vim.command("return {}".format(retstr))


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


def log_to_file():
    return vim.eval("g:vim_lsp_log_to_file") == "1"


def clear_signs(filename):
    vim.command("sign unplace * file={}".format(filename))

