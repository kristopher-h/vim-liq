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

Installation is done by downloading an extracting a release bundle, e.g. using pathogen::

    cd ~/.vim/bundle
    wget url_to_release.tgz
    tar xzf vim-liq.tgz

Note: Do not use git clone to clone the repo as that will leave you without any LSP servers. For
more information see the DEVELOMPENT.rst.

Currently LSP servers for the following languages are included:

#. python

Upgrading
~~~~~~~~~

To upgrade vim-liq simply remove the old vim-liq folder and redo the installation. Example::

    cd ~/.vim/bundle
    rm -r vim-liq

After that redo the installation.

Usage
-----

The plugin currently automatically map the following keybindings:

| **CTRL-Space** => completion (insert mode)
| **.** => completion (insert mode)
| **LEADER-d** => goto definition (normal mode)
| **LEADER-f** => find references (normal mode)

Diagnostics is automatically enabled and uses vim marks. When moving to a line with a diagnostics
mark the message for that line is displayed in the command-line.

Additional commands:

| **LspDiagnostics:** Display diagnostics in the quickfix window.
| **LspReferences:** Find all references for symbol under cursor. Display result in quickfix window.
| **LspDefinition:** Goto defintion. If more than one definition is found display result in quickfix window.
| **LspLog:** Display debuglogs from vim-liq.
| **LspSymbol:** Display symbols in current file.

Requirements
------------

* Vim with support for:

  - python (2.7)
  - autocommands
  - quickfix
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
