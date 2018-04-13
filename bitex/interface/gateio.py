"""Gateio Interface class."""
# pylint: disable=arguments-differ
# Import Built-Ins
import logging

import requests

# Import Homebrew
from bitex.exceptions import UnsupportedPairError
from bitex.api.REST.gateio import GateioREST
from bitex.interface.rest import RESTInterface
from bitex.utils import check_and_format_pair, format_with
from bitex.formatters import GateioFormattedResponse


# Init Logging Facilities
log = logging.getLogger(__name__)


class Gateio(RESTInterface):
    """Gateio REST API Interface Class.

    Since Gateio doesn't make an explicit differentiation between api versions,
    we do not use a version checker for this interface.
    """

    def __init__(self, **api_kwargs):
        """Initialize the Interface class instance."""
        super(Gateio, self).__init__('Gateio', GateioREST(**api_kwargs))

    def _get_supported_pairs(self):
        """Return a list of supported pairs."""
        resp=self.request('data.gateio.io/api2/1/pairs/')
        return [pair for pair in resp.json()]

    def request(self, endpoint, authenticate=False, **kwargs):
        """Generate a request to the API."""
        verb = 'POST' if authenticate else 'GET'
        return super(Gateio, self).request(verb, endpoint, authenticate=authenticate, **kwargs)

    ###############
    # Basic Methods
    ###############

    # Public Endpoints

    @check_and_format_pair # Gateio ticker response all pairs
    @format_with(GateioFormattedResponse)
    def ticker(self, pair, *args, **kwargs): # tickers is all pair ticker
        """Return the ticker for the given pair."""
        return self.request('api.gateio.io/api2/1/ticker/%s' % pair, params=kwargs)

    @check_and_format_pair
    @format_with(GateioFormattedResponse)
    def order_book(self, pair, *args, **kwargs): # orderBooks is all pair orderBook
        """Return the order book for the given pair."""
        return self.request('api.gateio.io/api2/1/orderBook/%s' % pair, params=kwargs)

    @check_and_format_pair
    @format_with(GateioFormattedResponse)
    def trades(self, pair, *args, **kwargs):
        """Return trades for the given pair."""
        raise NotImplementedError

    # Private Endpoints
    @check_and_format_pair
    @format_with(GateioFormattedResponse)
    def ask(self, pair, price, size, *args, market=False, **kwargs):
        """Place an ask order."""
        raise NotImplementedError

    @check_and_format_pair
    @format_with(GateioFormattedResponse)
    def bid(self, pair, price, size, *args, market=False, **kwargs):
        """Place a bid order."""
        raise NotImplementedError

    def _place_order(self, pair, price, size, side, market=None, **kwargs):
        """Place an order with the given parameters."""
        raise NotImplementedError

    @format_with(GateioFormattedResponse)
    def order_status(self, order_id, *args, **kwargs):
        """Return the order status for the given order's ID."""
        raise NotImplementedError

    @format_with(GateioFormattedResponse)
    def open_orders(self, *args, pair=None, **kwargs):
        """Return all open orders."""
        raise NotImplementedError

    @format_with(GateioFormattedResponse)
    def cancel_order(self, *order_ids, **kwargs):
        """Cancel existing order(s) with the given id(s)."""
        raise NotImplementedError

    @format_with(GateioFormattedResponse)
    def wallet(self, *args, **kwargs):
        return self.request('api.gateio.io/api2/1/private/balances/', authenticate=True, params=kwargs)

    ###########################
    # Exchange Specific Methods
    ###########################

