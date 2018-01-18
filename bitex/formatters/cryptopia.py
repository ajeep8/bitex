"""FormattedResponse Class for Standardized methods of the Cryptopia Interface class."""
# Import Built-ins
from datetime import datetime

# Import Home-brewed
from bitex.formatters.base import APIResponse


class CryptopiaFormattedResponse(APIResponse):
    """FormattedResponse class.

    Returns the standardized method's json results as a formatted data in a namedTuple.
    """

    def ticker(self, *args):
        """Return namedtuple with given data."""
        data = self.json(parse_int=str, parse_float=str)
        data = data["Data"]

        bid = data["BidPrice"]
        ask = data["AskPrice"]
        high = data["High"]
        low = data["Low"]
        last = data["LastPrice"]
        volume = data["Volume"]
        timestamp = datetime.utcnow()

        return super(CryptopiaFormattedResponse, self).ticker(bid, ask, high, low, last, volume,
                                                              timestamp)

    def order_book(self, bids, asks, ts):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def trades(self, trades, ts):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def bid(self, price, size, side, oid, otype, ts):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def ask(self, price, size, side, oid, otype, ts):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def order_status(self, *args):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def cancel_order(self, *args):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def open_orders(self, *args):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def wallet(self, *args):
        """Return namedtuple with given data."""
        raise NotImplementedError