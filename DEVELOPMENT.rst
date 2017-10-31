vim-liq development
===================

Todo
----

#. Clean up, refactor
#. Add documentation availible via help in vim
#. Add support for more lsp servers
#. Verify the plugin is working with vim built for python3 as well as 2
#. Add rename support
#. Automate release procedure
#. And much more

Development Requirements
------------------------

* git
* tox - for testing
* python3 - for creating a release 
* pip - for installing python LSP server (pyls)

Testing (for developers)
------------------------

Testing of the pythoncode is done with tox. So first make sure you have tox installed. E.g.::

    pip install tox

Optional: To install the supported language servers in the repo run::

    tools/create_release --dev

Once tox is installed simply run tox from the plugin folder of vim-liq::

    cd ~/path/to/vim-liq-repo/plugin
    tox

This will run unittests and linting (currently flake8 is used for linting).

There currently is no tests for the vimscript code.
