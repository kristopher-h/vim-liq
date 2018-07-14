#!/usr/bin/env python3
# Copyright 2017 Kristopher Heijari
#
# This file is part of vim-liq.
#
# vim-liq is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vim-liq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-liq.  If not, see <http://www.gnu.org/licenses/>.
"""Install the palantir python lsp server.  """

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
try:
    from urllib import urlretrieve as http_download
except ImportError:
    from urllib.request import urlretrieve as http_download
import zipfile

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

URL = "https://github.com/palantir/python-language-server/archive/0.21.2.zip"
UNZIPPED_NAME = "python-language-server-0.21.2"
ZIP_NAME = "python_lsp.zip"
INSTALL_DIR_NAME = "python_lsp_server"
DEFAULT_TARGET_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../plugin/servers/python/")


BACKPORTS_INIT = "__path__ = __import__('pkgutil').extend_path(__path__, __name__)\n"

PYLS_MAIN = """#!/usr/bin/env python
import glob
import os
import re
import sys

f_path = os.path.dirname(os.path.abspath(__file__))

if sys.version_info[0] >= 3:
    sitepack = glob.glob(os.path.join(f_path, "lib/python3.[0-9]/site-packages"))[0]
else:
    sitepack = os.path.join(f_path, "lib/python2.7/site-packages")

sys.path.insert(0, sitepack)

from pyls.__main__ import main

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
"""


def install(dest_dir, zipapp=False):
    """Install python lsp server from palantir."""

    tempdir = tempfile.mkdtemp()
    log.debug("Created temporary directory %s", tempdir)

    try:
        install_dir = os.path.join(tempdir, INSTALL_DIR_NAME)
        zip_path = os.path.join(tempdir, ZIP_NAME)
        log.debug("Downloading %s", URL)
        http_download(URL, filename=zip_path)
        with zipfile.ZipFile(zip_path, "r") as unzipit:
            log.debug("Unzipping %s to %s", zip_path, tempdir)
            unzipit.extractall(path=tempdir)

        extras = "[rope,yapf,mccabe,pyflakes,pycodestyle,pydocstyle]"
        # install for py2
        subprocess.check_call(
            ["pip2.7", "install", "--no-compile", "--prefix", install_dir, "--ignore-installed",
             "--upgrade", os.path.join(tempdir, UNZIPPED_NAME) + extras])
        # install for py3
        subprocess.check_call(
            ["pip3", "install", "--no-compile", "--prefix", install_dir, "--ignore-installed",
             "--upgrade", os.path.join(tempdir, UNZIPPED_NAME) + extras])

        # We need to create this init file since the import for configparser for python2
        # otherwise fails. Since the pth file in site-packages is not read. Note that adding the
        # path with "import site; site.addsite(...) does not seem to work either (guessing it is
        # due to the zipapp bundling).
        backports_init = os.path.join(install_dir,
                                      "lib/python2.7/site-packages/backports/__init__.py")
        pyls_main = os.path.join(install_dir, "__main__.py")

        with open(backports_init, "w") as file_:
            file_.write(BACKPORTS_INIT)

        with open(pyls_main, "w") as file_:
            file_.write(PYLS_MAIN)

        if zipapp:
            subprocess.check_call(
                ["python3", "-m", "zipapp", "-o", os.path.join(dest_dir, pylz.pyz),
                 "-p", "/usr/bin/env python", install_dir])
        else:
            pyls_dir = os.path.join(dest_dir, "pyls")
            if os.path.exists(pyls_dir):
                shutil.rmtree(pyls_dir)
            shutil.copytree(install_dir, pyls_dir)

    finally:
        # Always delete tempdir after finishing
        shutil.rmtree(tempdir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zipapp", action="store_true", help="Create a zipapp")
    parser.add_argument("--target", help="Target directory.", default=DEFAULT_TARGET_DIR)
    args = parser.parse_args()
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    install(args.target, args.zipapp)

if __name__ == "__main__":
    main()
