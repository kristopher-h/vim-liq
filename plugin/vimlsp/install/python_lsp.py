# Copyright 2017 Kristopher Heijari
#
# This file is part of vim-lsp.
#
# vim-lsp is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# vim-lsp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-lsp.  If not, see <http://www.gnu.org/licenses/>.
"""Install a the palantir python lsp server.  """
from __future__ import print_function

import fileinput
import glob
import logging
import os
import shutil
import subprocess
import tempfile
try:
    from urllib import urlretrieve as http_download
except:
    from urllib.request import urlretrieve as http_download
import zipfile

import pip

from . import LspInstallError

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

URL = "https://github.com/palantir/python-language-server/archive/master.zip"
ZIP_NAME = "python_lsp.zip"
UNZIPPED_NAME = "python-language-server-master"
INSTALL_DIR_NAME = "python_lsp_server"
THE_NASTY = """import site
site.addsitedir("{}")
"""

def install(dest_dir):
    """Install python lsp server from palantir."""

    tempdir = tempfile.mkdtemp()
    log.debug("Created temporary directory %s", tempdir)

    try:
        target_dir = os.path.join(dest_dir, INSTALL_DIR_NAME)
        if os.path.exists(target_dir):
            log.debug("Deleting %s", target_dir)
            shutil.rmtree(target_dir)
        INSTALL_DIR = os.path.join(tempdir, INSTALL_DIR_NAME)
        zip_path = os.path.join(tempdir, ZIP_NAME)
        log.debug("Downloading %s", URL)
        http_download(URL, filename=zip_path)
        with zipfile.ZipFile(zip_path, "r") as unzipit:
            log.debug("Unzipping %s to %s", zip_path, tempdir)
            unzipit.extractall(path=tempdir)


        pip.main(["install", "--prefix", INSTALL_DIR, "--ignore-installed", "--upgrade",
                  os.path.join(tempdir, UNZIPPED_NAME)])

        # Do the nasty, how can this possibly go wrong :-)
        glob_path = glob.glob(os.path.join(INSTALL_DIR, "lib/python*"))[0]
        python_dir = os.path.basename(os.path.normpath(glob_path))
        pyls_path = os.path.join(INSTALL_DIR, "bin/pyls")
        site_packages = os.path.join(dest_dir, INSTALL_DIR_NAME, "lib",
                                     python_dir, "site-packages")
        try:
            for line in fileinput.input(pyls_path, inplace=1):
                print(line, end="")
                if line == "import sys\n":
                    log.debug("Adding %s to pyls site-packages in %s", site_packages, pyls_path)
                    print(THE_NASTY.format(site_packages), end="")
        finally:
            fileinput.close()
        # end nastyness

        shutil.move(INSTALL_DIR, dest_dir)

    finally:
        # Always delete tempdir after finishing
        shutil.rmtree(tempdir)

    return {
        "python": {
            "start_cmd": os.path.join(target_dir, "bin/pyls"),
            "log_arg": "--log-file",
            "transport": "STDIO"
        }
    }

