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
"""Language server protocol base protocol implementation.

This module contains an implementation of the base protocol for the language server.

It implements a client with the possibility to write and read over stdout/stdin.
"""
import collections
import logging
import os
import subprocess

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ServerDead(Exception):
    """Raised if the connection with the server is dead."""


class StdIO(object):
    """Class providing read and write to stdin/stdout.

    This class spawns a subprocess and connects to stdin/stdout. Reading is done from the
    process stdout and writing to its stdin.
    """
    def __init__(self, start_cmd):
        self._start_cmd = start_cmd
        self._reader = None
        self._writer = None
        self._server = None

    def connect(self):
        """Connect to remote."""
        self._devnull = open(os.devnull, "w")
        # TODO: Add possibility to capture stderr or pipe to memlogger directly?
        self._server = subprocess.Popen(self._start_cmd, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self._devnull)
        self._reader = self._server.stdout
        self._writer = self._server.stdin

    def close(self):
        """Close connection and terminate remote."""
        self._server.kill()
        self._server.wait()

    def write(self, data):
        """Write data."""
        return self._writer.write(data)

    def read(self, size=-1):
        """Write data."""
        return self._reader.read(size)

    def readline(self, size=-1):
        """Read a line."""
        return self._reader.readline(size)

    def flush(self):
        """Flush data."""
        self._writer.flush()


class LspBaseMsg(object):
    """Lsp message.

    LSP base message.
    """
    def __init__(self, body, headers=None):
        """Create Message.

        Args:
            body (str): Message body.
            headers (dict): Header dict. If not provided one is created.
        """
        self.body = body
        if headers:
            self.headers = headers
        else:
            self.headers = collections.OrderedDict([
                ("Content-Type", "application/vscode-jsonrpc; charset=utf-8"),
                ("Content-Length", len(body)),
            ])

    def to_bytes(self):
        """Serialize message to bytes."""
        out = ["{}: {}".format(key, value) for key, value in self.headers.items()]
        out.append("\r\n")
        return "\r\n".join(out).encode("ascii") + self.body.encode("utf8")


class LspBase(object):
    """Lsp base protocol implementation."""
    def __init__(self, io, qsize=0, msg_handler=None):
        """Initialize LspBase.

        Args:
            io: File-like object implementing at least read, write, readline and close. The
                object should be open for reading/writing.
        """
        self._io = io

    def send(self, body):
        """Send message.

        body (Bytes): Message.
        """
        msg = LspBaseMsg(body)
        try:
            raw = msg.to_bytes()
            log.log(5, "Send: %s", raw)
            self._io.write(raw)
            self._io.flush()
        except (OSError, IOError) as exc:
            # This will happen if server dies
            log.error("Write to pipe failed. Exception: %s", exc)
            raise ServerDead(exc)

    def recv(self):
        """Read message.

        Returns:
            LspBaseMessage: If no message is availible return None.

        """
        msg = self._read()
        log.log(5, "Recv: %s", msg)
        return msg

    def _read(self):
        """Read from stdout."""
        # Read until a messages is received
        while True:
            # Read headers
            headers = {}
            # Read headers
            while True:
                try:
                    line = self._io.readline().decode("ascii")
                except (OSError, IOError) as exc:
                    # This will happen if server dies
                    log.error("Read from pipe failed. Exception: %s", exc)
                    # Consider dead.
                    raise ServerDead(exc)

                log.log(5, "readline: %s", line)

                if line == "":
                    raise ServerDead("EOF from server.")
                elif line == "\r\n":
                    # All headers read. Break header loop.
                    break
                elif line.endswith("\r\n"):
                    key, value = line.split(":")
                    headers[key.strip()] = value.strip()

            # Read Body
            read_len = int(headers["Content-Length"])
            try:
                body = self._io.read(read_len).decode("utf-8")
            except (OSError, IOError) as exc:
                raise ServerDead(exc)

            return body
