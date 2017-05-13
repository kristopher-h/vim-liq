#!/usr/bin/env python
import argparse
import json
import logging
import os
import sys

import vimlsp.install.python_lsp

log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

INSTALL_FUNCS = (
    vimlsp.install.python_lsp.install,
)

INSTALL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vimlsp_servers")

SERVER_JSON = "supported_servers.json"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Turn on debugging.")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    log.debug("Args: %s", args)
    if args.debug:
        log.setLevel(logging.DEBUG)

    if os.path.exists(INSTALL_DIR):
        if not os.path.isdir(INSTALL_DIR):
            raise OSError("File {} already exists but is not a directory.".format(INSTALL_DIR))
    else:
        os.mkdir(INSTALL_DIR)

    servers = {}
    if os.path.isfile(SERVER_JSON):
        with open(SERVER_JSON) as f:
            servers = json.load(f)


    for install in INSTALL_FUNCS:
        try:
            serv_info = install(INSTALL_DIR)
            servers.update(serv_info)

        except vimlsp.install.LspInstallError as exc:
            log.info("%s.%s failed with message: %s",
                     install.__module__, install.__name__, exc)

    with open(SERVER_JSON, "w") as f:
        json.dump(servers, f, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    main()
