vim-liq
=======

vim-liq is a vim client for the Language Server Protocol (LSP). vim-liq stands for something along
the lines of vim- "Language IQ" or "Lingustic Intelligence".

Development Status
------------------

This project is in a beta state and may not be suitable for general use. But for those
willing to tinker a bit it might be worth a try :-).

The following high level, LSP, features have support:

#. Completion
#. References
#. Diagnostics
#. Definition

Todo
----

#. Clean up, refactor
#. Add documentation availible via help in vim
#. Add support for more lsp servers
#. Verify the plugin is working with vim built for python3 as well as 2
#. Add rename support
#. And much more

Installation
------------

The instruction below is fairly untested but should work. It is only tested on osX and Linux.

LSP client
~~~~~~~~~~

First one must download the plugin. This can be done by the normal means, e.g. by using pathogen:

* [Pathogen](https://github.com/tpope/vim-pathogen)
  - `git clone https://github.com/kristopher-h/vim-liq ~/.vim/bundle/vim-liq`

LSP servers
~~~~~~~~~~~

Once the plugin is installed one or more language servers must be installed. To install
all supported language servers the following should do the trick::

    cd ~/.vim/bundle/vim-liq
    plugin/install_lsp_server.py

Currently only python language server is "supported", it is however possible to manually edit
the supported_servers.json file to test with other language servers as well. The file does not
exist until at least one lsp server has been installed. See plugin/supported_servers_example.json
for an example of what the contents of the file should look like.

Usage
-----

The plugin currently automatically map the following keybindings::

    CTRL-Space => completion
    . => completion
    LEADER-d => goto definition
    LEADER-f => find references

Diagnostics is automatically enabled and uses vim marks. When moving to a line with a diagnostics
mark the message for that line is displayed in the command-line.

Additional commands::

    LspDiagnostics: Display diagnostics in the quickfix window.
    LspReferences: Find all references for symbol under cursor. Display result in quickfix window.
    LspDefinition: Goto defintion. If more than one definition is found display result in quickfix
        window.
    LspLog: Display debuglogs from vim-liq.

Requirements
------------

* Vim with support for:

  - python (2.7)
  - autocommands
  - quickfix
  - possibly more without me knowing it?

* python > 2.7 (running/installing python-language-server)
* pytest, tox, mock for testing
* pip (for installing python-language-server)

Testing (for developers)
------------------------

Testing of the pythoncode is done with tox. So first make sure you have tox installed. E.g.::

    pip install tox

Once tox is installed simply run tox from the plugin folder of vim-liq::

    cd ~/.vim/bundle/vim-liq/plugin
    tox

This will run unittests and linting (currently flake8 is used for linting). As a part of testing
the lsp servers supported will be downloaded/installed locally in plugin/tests/.lsp_install_dir.
This is however only done the first time the test is run. To force a re-install one must manually
remove the .lsp_install_dir.

There currently is no tests for the vimscript code.

Credits
-------

Credits go to the following projects, without which it would have been much harder to create
this.

* jedi-vim (https://github.com/davidhalter/jedi-vim/)
* python-language-server (https://github.com/palantir/python-language-server)
* language-server-protocol (https://github.com/Microsoft/language-server-protocol/)
* LanguageClient-neovim (https://github.com/autozimu/LanguageClient-neovim)
* vim-plugin-starter-kit (https://github.com/JarrodCTaylor/vim-plugin-starter-kit)

License
-------

GPLv3 or later.
