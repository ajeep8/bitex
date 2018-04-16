"""Kraken Interface class."""
# Import Built-Ins
import logging

# Import Homebrew
from bitex.api.REST.kraken import KrakenREST
from bitex.interface.rest import RESTInterface
from bitex.utils import check_and_format_pair, format_with
from bitex.formatters import KrakenFormattedResponse

# Init Logging Facilities
log = logging.getLogger(__name__)


class Kraken(RESTInterface):
    """Kraken Interface class."""

    def __init__(self, **api_kwargs):
        """Initialize Interface class instance."""
        super(Kraken, self).__init__('Kraken', KrakenREST(**api_kwargs))

    def _get_supported_pairs(self):
        """Return a list of supported pairs."""
        r = self.request('AssetPairs').json()['result']
        return [r[k]['base'] + r[k]['quote'] if r[k]['base'] != 'BCH'
                else k for k in r]

    def _get_supported_pairs_formatted(self):
        """Return a list of supported pairs."""
        raise NotImplementedError

    # pylint: disable=arguments-differ
    def request(self, endpoint, authenticate=False, **req_kwargs):
        """Generate a request to the API."""
        if authenticate:
            return super(Kraken, self).request('POST', 'private/' + endpoint,
                                               authenticate=True, **req_kwargs)
        return super(Kraken, self).request('GET', 'public/' + endpoint, authenticate=False,
                                           **req_kwargs)

    # Public Endpoints
    # pylint: disable=arguments-differ
    # @format_with(KrakenFormattedResponse)
    @check_and_format_pair
    @format_with(KrakenFormattedResponse)
    def ticker(self, *pairs, **kwargs):
        """Return the ticker for the given pair."""
        payload = {'pair': pairs}
        payload.update(kwargs)
        return self.request('Ticker', params=payload)

    @check_and_format_pair
    @format_with(KrakenFormattedResponse)
    def order_book(self, pair, *args, **kwargs):
        """Return the order book for the given pair."""
        payload = {'pair': pair}
        payload.update(kwargs)
        return self.request('Depth', params=payload)

    @check_and_format_pair
    @format_with(KrakenFormattedResponse)
    def trades(self, pair, *args, **kwargs):
        """Return the trades for the given pair."""
        payload = {'pair': pair}
        payload.update(kwargs)
        return self.request('Trades', params=payload)

    # Private Endpoints
    def _place_order(self, pair, price, size, side, **kwargs):
        """Place an order with the given parameters."""
        payload = {'pair': pair, 'type': side, 'ordertype': 'limit',
                   'price': price, 'volume': size}
        payload.update(kwargs)
        return self.request('AddOrder', authenticate=True, data=payload)

    @check_and_format_pair
    @format_with(KrakenFormattedResponse)
    def ask(self, pair, price, size, *args, **kwargs):
        """Place an ask order."""
        return self._place_order(pair, price, size, 'sell', **kwargs)

    @check_and_format_pair
    @format_with(KrakenFormattedResponse)
    def bid(self, pair, price, size, *args, **kwargs):
        """Place a bid order."""
        return self._place_order(pair, price, size, 'buy', **kwargs)

    @format_with(KrakenFormattedResponse)
    def order_status(self, order_id, *args, **kwargs):
        """Return the order status of the order with given ID."""
        raise NotImplementedError

    @format_with(KrakenFormattedResponse)
    def open_orders(self, *args, **kwargs):
        """Return all open orders."""
        return self.request('OpenOrders', authenticate=True, data=kwargs)

    @format_with(KrakenFormattedResponse)
    def cancel_order(self, *order_ids, **kwargs):
        """Cancel order(s) with the given ID(s)."""
        results = []
        payload = kwargs
        for oid in order_ids:
            payload.update({'txid': oid})
            r = self.request('CancelOrder', authenticate=True, data=payload)
            results.append(r)
        return results if len(results) > 1 else results[0]

    @format_with(KrakenFormattedResponse)
    def wallet(self, *args, **kwargs):
        """Return the account's wallet."""
        return self.request('Balance', authenticate=True, data=kwargs)
