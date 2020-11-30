import html.parser
import urllib.request
import logging
from typing import Optional, List, Dict

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


class NeweggParser(html.parser.HTMLParser):

    # We set this flag to True once we encounter an item cell.
    # <div class="item-cell">
    _encountered_item: bool = False

    # We set this flag to True if we're within an item cell and encounter the title.
    # <div class="item-cell">
    #   ...
    #   <a class="item-title">
    _encountered_title: bool = False

    # Tracking the depth of how many layers of tags we're currently in.
    # Specifically, once we hit an item cell, we want to know how deep we are, such that
    # if we hit an end tag that's the same depth, we know we've exited the item cell.
    _depth: int = 1

    # Storing the value of self._depth once we've encountered an item.
    _item_depth: Optional[int] = None

    # Storing the current product title.
    _title: Optional[str] = None

    # Storing the items and if they're in stock.
    items: Dict[str, bool] = {}

    def __init__(self, base_url: str):
        html.parser.HTMLParser.__init__(self)
        self._base_url = base_url

    def handle_starttag(self, tag, attrs):
        # Always increment depth.
        self._depth += 1

        # Did we hit an item?
        if tag == 'div' and ('class', 'item-cell') in attrs:
            self._encountered_item = True
            self._item_depth = self._depth

        # Are we in an item-cell, and is this the element of the item's title?
        if self._encountered_item and tag == 'a' and ('class', 'item-title') in attrs:
            self._encountered_title = True

    def handle_data(self, data):
        # If we find an item's title within its cell, add it to the items dict. Assume
        # it's in stock until (very shortly later) proven otherwise.
        if self._encountered_title and self._encountered_item:
            self._title = data
            self.items[data] = True
            LOGGER.debug("Found product: %s", data)
        if data == 'OUT OF STOCK':
            self.items[self._title] = False
            LOGGER.debug("Out of stock : %s", self._title)

    def handle_endtag(self, tag):
        # Always decrement depth.
        self._depth -= 1

        # Always assume we're out of a title element.
        self._encountered_title = False

        # Did we exit an item-cell?
        if self._encountered_item and self._depth == self._item_depth:
            self._encountered_item = False

    def fetch(self):
        """
        Fetch data from provided URL and start parsing.
        """
        with urllib.request.urlopen(self._base_url) as f:
            self.feed(f.read().decode('utf-8'))
    
    def get_items_in_stock(self) -> List[str]:
        """
        After parsing the page, return a list of items in stock.
        """
        return [item for item, avail in self.items.items() if avail]


if __name__ == "__main__":
    # Setup console logging if running interactively.
    LOGGER.addHandler(logging.StreamHandler())

    # Do the thing.
    parser = NeweggParser('https://www.newegg.com/p/pl?d=gtx+3070&N=100007709&isdeptsrh=1&PageSize=96')
    parser.fetch()
    print(parser.get_items_in_stock())

