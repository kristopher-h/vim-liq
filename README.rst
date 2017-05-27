vim-lsp
=======

vim-lsp is a vim client for the language server protocol.

Development Status
------------------

This project is in a early alpha state and is not yet suitable for general use.

Todo
----

1. It is now due time to refactor, refactor, clean-up and refactor
2. Add unit tests (start with all python code)
3. Add support for more lsp servers
4. Verify python3 and python2 support

Credits
-------

Credits go to the following projects, without which it would have been much harder to create
this.

* jedi-vim (https://github.com/davidhalter/jedi-vim/)
* python-language-server (https://github.com/palantir/python-language-server)
* language-server-protocol (https://github.com/Microsoft/language-server-protocol/)
* LanguageClient-neovim (https://github.com/autozimu/LanguageClient-neovim)
* vim-plugin-starter-kit (https://github.com/JarrodCTaylor/vim-plugin-starter-kit)

Requirements
------------

* Vim with support for:
  - python (2.7)
  - autocommands
  - quickfix
  - possible more without me knowing it?
* python > 2.7 (running/installing python-language-server)
* pip (for installing python-language-server)

Installation
------------

TBD
At some point the instruction below should work, but for now it is completly untested and is more
kept as a reminder of how it should be.

LSP client
~~~~~~~~~~

First one must download the plugin. This can be done by the normal means:

* [Pathogen](https://github.com/tpope/vim-pathogen)
  - `git clone https://github.com/kristopher-h/vim-lsp ~/.vim/bundle/vim-lsp`
* [Vundle](https://github.com/gmarik/vundle)
  - Add `Bundle 'https://github.com/kristopher-h/vim-lsp'` to .vimrc
  - Run `:BundleInstall`
* [NeoBundle](https://github.com/Shougo/neobundle.vim)
  - Add `NeoBundle 'https://github.com/kristopher-h/vim-lsp'` to .vimrc
  - Run `:NeoBundleInstall`
* [vim-plug](https://github.com/junegunn/vim-plug)
  - Add `Plug 'https://github.com/kristopher-h/vim-lsp'` to .vimrc
  - Run `:PlugInstall`

LSP servers
~~~~~~~~~~~

Once the plugin is installed one or more language servers must be installed. To install
all supported language servers the following should do the trick::

    cd ~/.vim/bundle/vim-lsp
    plugin/install_lsp_server.py

Currently only python language server is supported.

License
-------

GPLv3 or later.
