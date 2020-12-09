import html.parser
import urllib.request
import logging
import json
import io
from enum import Enum, auto
from typing import Optional, List, Dict, Collection, Tuple

import boto3
from botocore import exceptions

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class Status(Enum):
    NO_CHANGE = auto()
    INITIALIZED = auto()
    ITEMS_IN_STOCK = auto()
    ITEMS_GONE = auto()


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
        if tag == "div" and ("class", "item-cell") in attrs:
            self._encountered_item = True
            self._item_depth = self._depth

        # Are we in an item-cell, and is this the element of the item's title?
        if self._encountered_item and tag == "a" and ("class", "item-title") in attrs:
            self._encountered_title = True

    def handle_data(self, data):
        # If we find an item's title within its cell, add it to the items dict. Assume
        # it's in stock until (very shortly later) proven otherwise.
        if self._encountered_title and self._encountered_item:
            self._title = data
            self.items[data] = True
            LOGGER.debug("Found product: %s", data)
        if data == "OUT OF STOCK":
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
            self.feed(f.read().decode("utf-8"))

    def get_items(self) -> Dict[str, bool]:
        """
        After parsing the page, return a dict of the items and their stock status.
        """
        return self.items


def compare_to_s3(
    current_items: Dict[str, bool], s3_bucket: str, s3_obj: str
) -> Tuple[Status, Collection[str]]:
    """
    Diff the results against the previous state in S3, then update S3.
    """
    s3 = boto3.resource("s3")
    status = Status.NO_CHANGE

    # Retrieve existing dict, or instantiate an empty one if it doesn't exist in S3.
    obj = s3.Bucket(s3_bucket).Object(s3_obj)
    try:
        existing_items = json.load(obj.get()["Body"])
    except exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            existing_items = {}
            status = Status.INITIALIZED
        else:
            raise e

    # If our items haven't changed, just exit. A PutObject operation is more costly.
    if current_items == existing_items:
        return (status, set())

    # Are there new in-stock items compared to last time?
    in_stock_current = set(
        [item for item, in_stock in current_items.items() if in_stock]
    )
    in_stock_previous = set(
        [item for item, in_stock in existing_items.items() if in_stock]
    )

    # Need to update our object now.
    with io.BytesIO(json.dumps(current_items).encode("utf-8")) as fp:
        obj.upload_fileobj(fp)

    # Return a set of any new items.
    diff = in_stock_current - in_stock_previous
    if diff and (status != Status.INITIALIZED):
        status = Status.ITEMS_IN_STOCK
    if (not diff) and in_stock_previous:
        status = Status.ITEMS_GONE
    return (status, diff)


def send_init_message(
    sns, topic_arn: str, checker_name: str, stock_changes: Collection[str]
):
    stock_changes_lines = "\n".join(stock_changes)
    subject = f"[{checker_name}] - First run successful"
    message = f"Stock checker operational. Items in stock:\n{stock_changes_lines}"
    sns.publish(TopicArn=topic_arn, Message=message, Subject=subject)


def send_in_stock_message(
    sns, topic_arn: str, checker_name: str, stock_changes: Collection[str]
):
    stock_changes_lines = "\n".join(stock_changes)
    subject = f"[{checker_name}] - New items in stock!"
    message = f"Hurry up! New items in stock:\n{stock_changes_lines}"
    sns.publish(TopicArn=topic_arn, Message=message, Subject=subject)


def send_gone_message(sns, topic_arn: str, checker_name: str):
    subject = f"[{checker_name}] - All items gone!"
    message = f"Too slow..."
    sns.publish(TopicArn=topic_arn, Message=message, Subject=subject)


def lambda_handler(event, context):
    parser = NeweggParser(event["url"])
    parser.fetch()
    items = parser.get_items()

    # Continue to print in-stock items to the logs.
    for item, in_stock in items.items():
        if in_stock:
            LOGGER.info(item)

    # Compare to S3 and update.
    status, stock_changes = compare_to_s3(items, event["s3Bucket"], event["s3Object"])

    # Return immediately if no change.
    if status == Status.NO_CHANGE:
        return

    # Otherwise send SNS message.
    sns = boto3.client("sns", region_name="us-east-1")
    if status == Status.INITIALIZED:
        send_init_message(sns, event["topicArn"], event["s3Object"], stock_changes)
    if status == Status.ITEMS_IN_STOCK:
        send_in_stock_message(sns, event["topicArn"], event["s3Object"], stock_changes)
    if status == Status.ITEMS_GONE:
        send_gone_message(sns, event["topicArn"], event["s3Object"])


if __name__ == "__main__":
    # Setup console logging if running interactively.
    LOGGER.addHandler(logging.StreamHandler())

    # Do the thing.
    event = {
        "url": "https://www.newegg.com/p/pl?d=gtx+3070&N=100007709&isdeptsrh=1&PageSize=96",
        "topicArn": "arn:aws:sns:us-east-1:255595642331:newegg-stock-checker-20201204064825927800000001",
        "s3Bucket": "io-github-davidjoliver86-newegg-20201207070747933700000001",
        "s3Object": "derp",
    }
    lambda_handler(event, None)
