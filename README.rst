.. image:: https://travis-ci.org/kristopher-h/vim-liq.svg?branch=master
    :target: https://travis-ci.org/kristopher-h/vim-liq

vim-liq
=======

vim-liq is a vim client for the Language Server Protocol (LSP). vim-liq stands for something along
the lines of vim- "Language IQ" or "Lingustic Intelligence".

This project is in a beta state and may not be suitable for general use. But for those
willing to tinker a bit it might be worth a try :-).

Features
--------

The following high level, LSP, features have support:

#. Completion
#. References
#. Diagnostics
#. Definition
#. Symbols

Installation
------------

The instruction below is only tested on osX and Linux.

Installation is done by downloading an extracting a release bundle, example::

    mkdir -p ~/.vim/pack/plugins/start
    cd ~/.vim/pack/plugins/start
    wget https://github.com/kristopher-h/vim-liq/releases/latest
    tar xzf vim-liq.tgz

.. NOTE::
    Do not use git clone to clone the repo as that will leave you without any LSP servers. For
    more information see the DEVELOMPENT.rst.

Currently LSP servers for the following languages are included:

#. python

To add/overwrite language servers add the following in your .vimrc::

    let g:langIQ_servers = {}
    let g:langIQ_servers["<language>"] = {"cmd": "<start command>"}

Example::

    let g:langIQ_servers = {}
    let g:langIQ_servers["python"] = {"cmd": "pyls"}
    let g:langIQ_servers["rust"] = {"cmd": "rustup run beta rls"}

.. NOTE::
    When adding custom servers expect compatibility issues. This since the only language server 
    that has been used during development/testing is the bundled one.

Upgrading
~~~~~~~~~

To upgrade vim-liq simply remove the old vim-liq folder and redo the installation. Example::

    cd ~/.vim/pack/plugins/start
    rm -r vim-liq

After that follow the installation instruction again.

Usage
-----

The plugin by default map the following keybindings:

| **CTRL-Space** => completion (insert mode)
| **.** => completion (insert mode)
| **LEADER-d** => goto definition (normal mode)
| **LEADER-f** => find references (normal mode)

To disbale the default keymap set the following in your .vimrc::

    let g:langIQ_disablekeymap = 1

Diagnostics is automatically enabled and uses vim signs. When moving to a line with a diagnostics
mark the message for that line is displayed in the command-line.

To disable the usage of signs set the following in your .vimrc::

    let g:langIQ_disablesigns = 1

Additional commands:

| **LspDiagnostics:** Display diagnostics in the quickfix window.
| **LspReferences:** Find all references for symbol under cursor. Display result in quickfix window.
| **LspDefinition:** Goto defintion. If more than one definition is found display result in quickfix window.
| **LspLog:** Display debuglogs from vim-liq.
| **LspSymbol:** Display symbols in current file.

Requirements
------------

* Vim 8, or later, with support for:

  - python (2.7)
  - autocommands
  - quickfix
  - timers
  - async calls
  - possibly more without me knowing it?

* python > 2.7 (for running the python language server)

Credits
-------

Credits go to the following projects, without which it would have been much harder to create
this.

* jedi-vim (https://github.com/davidhalter/jedi-vim/)
* python-language-server (https://github.com/palantir/python-language-server)
* language-server-protocol (https://github.com/Microsoft/language-server-protocol/)
* LanguageClient-neovim (https://github.com/autozimu/LanguageClient-neovim)
* vim-plugin-starter-kit (https://github.com/JarrodCTaylor/vim-plugin-starter-kit)
* Pathogen (https://github.com/tpope/vim-pathogen)

License
-------

GPLv3 or later.
