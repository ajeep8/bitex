"""FormattedResponse Class for Standardized methods of the Gateio Interface class."""
# Import Built-ins
from datetime import datetime

# Import Home-brewed
from bitex.formatters.base import APIResponse


class GateioFormattedResponse(APIResponse):
    """FormattedResponse class.

    Returns the standardized method's json results as a formatted data in a namedTuple.
    """

    def ticker(self):
        """Return namedtuple with given data."""
        data = self.json(parse_int=str, parse_float=str)

        bid = data["highestBid"]
        ask = data["lowestAsk"]
        high = data["high24hr"]
        low = data["low24hr"]
        last = data["last"]
        volume = data["quoteVolume"]    # "quoteVolume"
        timestamp = datetime.utcnow()
        return super(GateioFormattedResponse, self).ticker(bid, ask, high, low, last, volume,
                                                           timestamp)

    def order_book(self):
        """Return namedtuple with given data."""
        data = self.json()
        asks = []
        bids = []
        for i in data['asks'][::-1]:
            asks.append([float(i[0]), float(i[1])])
        for i in data['bids']:
            bids.append([float(i[0]), float(i[1])])
        timestamp = datetime.utcnow()
        return super(GateioFormattedResponse, self).order_book(bids, asks, timestamp)

    def trades(self):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def bid(self):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def ask(self):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def order_status(self):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def cancel_order(self):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def open_orders(self):
        """Return namedtuple with given data."""
        raise NotImplementedError

    def wallet(self):
        """Return namedtuple with given data."""
        data = self.json(parse_int=str, parse_float=str)['available']
        balances = {}
        for i in data:
            if (i == 'BTC') | (i == 'USD') | (float(data[i]) > 0):
                balances[i] = float(data[i])
        return super(GateioFormattedResponse, self).wallet(balances, self.received_at)