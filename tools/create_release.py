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
"""Create a vim-liq release tgz.

This script should be run from the root of the vim-liq repository.
"""

import argparse
import os
import subprocess
import tarfile

CURRENT_DIR = os.path.dirname(__file__)
INSTALL_PYTHON_LSP = os.path.join(CURRENT_DIR, "create_portable_pyls.py")


def create_release(development=False):
    """Create a vim-liq release.

    Args:
        development(bool): If True create a tgz with the vim-liq release.

    Returns:
        str: Path to release file.
    """
    def exclude_files(filename):
        """Return True if filename should be excluded."""
        return filename in ["./.git"]

    # Install LSP servers
    subprocess.run(INSTALL_PYTHON_LSP, check=True)

    tar_name = ""
    if not development:
        # Cleanup all irrelevant files and folders
        cmd = "git clean -fdx --exclude=plugin/servers"
        subprocess.run(cmd, shell=True)
        # Create release zip in current folder
        tar_name = "vim-liq.tgz"
        with tarfile.open(tar_name, "w:gz") as tar:
            tar.add(".", arcname="vim-liq", exclude=exclude_files)

    return tar_name


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dev", action="store_true", help="Just install LSP servers, without creating tgz.")
    args = parser.parse_args()
    print(create_release(args.dev))


if __name__ == "__main__":
    main()
