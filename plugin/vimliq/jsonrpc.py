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
import json
import logging
import threading
try:
    import Queue as queue
except ImportError:
    import queue

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

METHOD = "method"
JSONRPC = "jsonrpc"
PARAMS = "params"
ID = "id"
RESULT = "result"
ERROR = "error"


class JsonRpcException(Exception):
    """Raise on failures."""


class JsonRpcError(JsonRpcException):
    """Raised when an error reply is received from the json rpc server."""

# TODO: Do proper parsing of jsonrpc messages separated from the class below. Rename JsonRpc
# class to something else (since json rpc is the protocol name). Maybe JsonRpcDispatcher...


class JsonRpc(object):
    """Json RPC class.

    Streaming json rpc class. The class supports both blocking and non blocking calls.
    Non blocking calls requires a callback to be passed in. The callback is called from
    the "read thread".
    """

    def __init__(self, transport):
        """Create a JsonRpc object.

        Args:
            transport: A object implementing "send(msg: str) and "recv() -> str". Where
                str in both cases represents a json rpc message as a string.
        """
        self._io = transport
        self._id = 34
        # _sync_id, _resp_map, _notification_map and _sync_id are all used in multiple threads
        # This is done since the read and write operations used are atomic.
        # See https://docs.python.org/3.7/faq/library.html#id17 for details.
        self._resp_map = {}
        self._notification_map = {}
        self._read_thread = threading.Thread(target=self._msg_handler)
        self._read_thread.daemon = True
        self._read_thread.start()
        self._sync_queue = queue.Queue()
        self._sync_id = None

    def register_notification_handler(self, method, handler):
        self._notification_map[method] = handler

    def call(self, method, params, notify=False):
        id_ = None if notify else self._get_id()
        self._send(method, params, id_)
        self._sync_id = id_
        try:
            response = self._sync_queue.get()
        except queue.Empty:
            response = (None, JsonRpcException("Timeout while waiting for sync reply"))
        # If an exception is set raise it
        # See msg_handler for details
        if response[1]:
            raise response[1]
        self._sync_id = None
        return response[0]

    def call_async(self, method, params, notify=False, callback=None):
        id_ = None if notify else self._get_id()
        if callback:
            self._resp_map[id_] = callback
        self._send(method, params, id_)

    def _send(self, method, params, id_=None):
        """Send a message.

        This is a non blocking call. Use recv to get replies. And use the provided
        id to correlate the messages.

        Args:
            id: (str|int|None): Identifier to correlate requests and response. If set to
                None, no id is included, and the request is considered a notification.
            method (str): The remote procedure to call.
            params (dict): JSON RPC params as a dict.

        """
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        if id_:
            msg["id"] = id_

        self._io.send(json.dumps(msg))

    def _msg_handler(self):
        """Msg handler."""
        while True:
            try:
                msg = json.loads(self._io.recv())
            except Exception as exc:  # pylint: disable=broad-except
                log.error("Got exception from on when reading. Giving up. Exception: %s", exc)
                # Returning will end the read thread
                return
            id_ = msg.get(ID)
            # Requese
            if id_:
                result = msg.get(RESULT)
                error = msg.get(ERROR)
                exception = JsonRpcError(error) if error else None

                if id_ == self._sync_id:
                    self._sync_queue.put((result, exception))

                else:
                    handler = self._resp_map.pop(id_, None)
                    if not handler:
                        log.warning("Unsolisitated response. id=%s, msg=%s", id_, msg)
                    else:
                        handler(result, exception)

            # Notification
            else:
                method = msg.get(METHOD)
                try:
                    self._notification_map[method](msg[PARAMS], None)
                except KeyError:
                    log.info("Unsupprted notification received. msg=%s", msg)

    # Private functions
    def _get_id(self):
        """Get unique request id."""
        self._id += 1
        return self._id
