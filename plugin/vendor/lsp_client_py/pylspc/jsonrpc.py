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
import copy
import json
import logging
import os
import subprocess
import sys
import threading
import time
try:
    # py3
    import queue
except ImportError:
    # py2
    import Queue as queue

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class JsonRpcException(Exception):
    """Base class for others."""


class JsonRpcReadTimeout(JsonRpcException):
    """Timeout when reading synchronized."""


class ReadThreadDead(JsonRpcException):
    """Raised if the read thread is dead."""

class ServerDead(JsonRpcException):
    """Raised if the connection with the server is dead."""


class JsonRpcBase(object):
    def __init__(self, start_cmd, msg_handler=None):
        """Initialize object.

        Args:
            start_cmd (list): Start command as a list, e.g. as accepted by Popen
            msg_handler(callable): Callable accepting one argument. E.g. a function fulfilling
              the following signature: "def handle(msg)". The msg is a jsonrpc message formatted
              to a dict. If set to None all unsolicitated messages are dropped. The msg_handler
              is called from an internal thread.
        """
        self._start_cmd = start_cmd
        self._server = None
        self._handler = None
        self.server_start()
        self._handler = JsonRpcHandler(self.writer, self.reader, msg_handler)

    def call(self, method, params, timeout=120):
        """Write message.

        The content-length header is automatically calculated and added before writing.
        """
        try:
            return self._handler.call(method, params, timeout=timeout)
        except JsonRpcException:
            self.stop()
            raise

    def notify(self, method, params):
        try:
            self._handler.notify(method, params)
        except ServerDead:
            self.stop()

    def stop(self):
        """stop server."""
        raise NotImplementedError("BaseClass must implement")

    def server_start(self):
        """Start server."""
        raise NotImplementedError("Sub class must implement")

    @property
    def reader(self):
        """File like object. Implement in subclass."""
        raise NotImplementedError("Sub class must implement")

    @property
    def writer(self):
        """File like object. Implement in subclass."""
        raise NotImplementedError("Sub class must implement")


class JsonRpcStdInOut(JsonRpcBase):
    """Language server client using a "pipe" for reading and writing."""
    def server_start(self):
        # Send stderr to devnull for now
        self._devnull = open(os.devnull, "w")
        log.debug("Starting JsonRpcStdInOut with cmd: %s", self._start_cmd)
        self._server = subprocess.Popen(self._start_cmd, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self._devnull)
        self._reader = self._server.stdout
        self._reader_err = self._server.stderr
        self._writer = self._server.stdin

    def stop(self):
        self._devnull.close()
        if self.is_alive():
            self._server.kill()
            self._server.wait()

    def is_alive(self):
        return self._server.returncode is None

    @property
    def writer(self):
        return self._writer

    @property
    def reader(self):
        return self._reader


class JsonRpcHandler(object):
    """JsonRpcHandler, supporting read and write."""

    def __init__(self, writer, reader, msg_handler=None):
        """
        Args:
            writer: file like object used to write to
            reader: file like object used to read from (in its own thread)
            msg_handler(callable): Callable accepting one argument. E.g. a function fulfilling
              the following signature: "def func(msg)". The msg is a jsonrpc message formatted
              to a dict. If set to None all unsolicitated messages are dropped. The msg_handler
              is called from an internal thread.

        """
        self.id = 155  # start at "something above 1" to avoid conflict
        self._writer = writer

        self._queue_condition = threading.Condition()
        self._sync_queue = {}
        self._async_queue = {}
        self._reader = reader
        self._read_thread = threading.Thread(target=self._non_blocking_read)
        self._read_thread.daemon = True
        self._read_thread.start()
        self._msg_handler = msg_handler

    def get_id(self):
        self.id += 1
        return self.id

    def call(self, method, params, timeout=120, callback=None):
        """Call a remote method.

        Args:
            method(str):
            params(dict):
            callback: callable accepting one argument (dict), if None run in synchronized mode.

        Returns:
            dict: If callback is set return None
        """
        id_ = self.get_id()
        request = {
            "method": method,
            "jsonrpc": "2.0",
            "id": id_,
        }
        if params is not None:
            request["params"] = params
        # Using condition here even if it isn't strictly neccarry since adding a value to
        # a dict is thread safe.
        with self._queue_condition:
            if callback:
                self._async_queue[id_] = callback
            else:
                self._sync_queue[id_] = None

        self.write(request)

        # Just return if it was an async call
        if callback:
            return

        start_time = time.time()
        with self._queue_condition:
            while (time.time() - start_time) < timeout:
                self._queue_condition.wait(timeout=timeout)
                if id_ in self._sync_queue:
                    response = self._sync_queue[id_]
                    del self._sync_queue[id_]
                    return response
            else:
                # Not interested anymore
                del self._sync_queue[id_]
                log.debug("No reply in %s sec for request %s", timeout, request)
                raise JsonRpcReadTimeout("No reply from server in {} sec.".format(timeout))

    def notify(self, method, params):
        request = {
            "method": method,
            "jsonrpc": "2.0",
        }
        if params is not None:
            request["params"] = params
        self.write(request)

    def write(self, data):
        """Write a request."""
        content = json.dumps(data)
        headers = "Content-Length: {}\r\n\r\n".format(len(content))
        out = headers.encode("ascii") + content.encode("utf8")

        log.debug("Writing: %s", out)
        try:
            self._writer.write(out)
            self._writer.flush()
        except (OSError, IOError) as exc:
            # This will happen if server dies
            log.debug("Read from pipe failed. Exception: %s", exc)
            # TODO: Verify that is_alive returns False efter this
            raise ServerDead(exc)


    def _non_blocking_read(self):
        reader = self._reader
        """Read a request put on queue when done."""
        log.debug("Reading non blocking")
        while True:
            # Just read stderr and log
            headers = {}
            # Read headers
            while True:
                try:
                    line = reader.readline().decode("ascii")
                except (OSError, IOError) as exc:
                    # This will happen if server dies
                    log.debug("Read from pipe failed. Exception: %s", exc)
                    # Consider this dead
                    return
                if line == "":
                    # EOF, this exits the thread
                    return
                elif line == "\r\n":
                    break
                elif line.endswith("\r\n"):
                    key, value = line.split(":")
                    headers[key.strip()] = value.strip()

            # Read Body
            read_len = int(headers["Content-Length"])
            try:
                body = reader.read(read_len)
            except (OSError, IOError) as exc:
                # This will happen if server dies
                log.debug("Read from pipe failed. Exception: %s", exc)
                # Consider this dead
                return
            msg = json.loads(body.decode("utf-8"))
            log.debug("Message received: %s", msg)

            # Response
            callback = None
            if "result" in msg or "error" in msg:
                id_ = msg["id"]
                with self._queue_condition:
                    # Sync
                    if id_ in self._sync_queue:
                        self._sync_queue[id_] = msg
                        self._queue_condition.notify()
                        continue
                    elif id_ in self._async_queue:
                        callback = self._async_queue[id_]
                        del self._async_queue[id_]

                # We only get here if it is an async call with a callback
                if callback:
                    callback(msg)
                    continue
                else:
                    log.debug("Response with unwanted id, %s, received.", id_)
                    continue

            elif "method" in msg:
                # # Request
                # if "id" in msg:
                #     pass
                # # Notification
                # else:
                #     pass
                # Handle notification and request in the same way. The handler has to take
                # care of the difference.
                if self._msg_handler:
                    self._msg_handler(msg)
            else:
                log.debug("Unknown message received.")
