import client
import vimutils as V


class ClientManager(object):
    """Class managing all clients."""

    def __init__(self):
        """Initialize object.

        Args:
            supported_clients(dict): See supported_clients.json

        Attributes:
            clients(dict): Dict where key is the language and value is the client object.
        """
        self._supported_clients = supported_clients
        self.clients = {}

    def shutdown_all(self):
        """Called when vim closes."""
        for _, client in self.clients.items():
            client.shutdown()

    def __getattr__(self):
        """Forward function call to the correct lsp client."""
        filetype = V.filetype()
