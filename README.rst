vim-liq
=======

vim-liq is a vim client for the language server protocol.

Development Status
------------------

This project is in an early alpha state and is may not be suitable for general use.

The following high level features have some level of support:

1. Auto complete
2. Find references
3. Diagnostics
4. Goto definition

Todo
----

1. It is now due time to refactor, refactor, clean-up and refactor
2. Add unit tests (start with all python code)
3. Add support for more lsp servers
4. Verify python3 and python2 support
6. Make sure python exceptions are handled better
5. and much more

Installation
------------

At some point the instruction below should work, for now it is mostly untested.

LSP client
~~~~~~~~~~

First one must download the plugin. This can be done by the normal means, e.g. by using pathogen:

* [Pathogen](https://github.com/tpope/vim-pathogen)
  - `git clone https://github.com/kristopher-h/vim-liq ~/.vim/bundle/vim-liq`

LSP servers
~~~~~~~~~~~

Once the plugin is installed one or more language servers must be installed. To install
all supported language servers the following should do the trick::

    cd ~/.vim/bundle/vim-liq/plugin
    python install_lsp_server.py

Currently only python language server is supported.

Requirements
------------

* Vim with support for:

  - python (2.7)
  - autocommands
  - quickfix
  - possibly more without me knowing it?
    
* python > 2.7 (running/installing python-language-server)
* pip (for installing python-language-server)

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
