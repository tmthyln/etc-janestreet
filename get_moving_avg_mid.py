#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="SEEKINGALPHA"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())


# ~~~~~============== HELPER FUNCTIONS ==============~~~~~

def write_and_read(exchange, command):
    write_to_exchange(exchange, command)
    exchange_reply = read_from_exchange(exchange)
    print("The exchange replied:", exchange_reply, file=sys.stderr)


# ~~~~~============== TRADING LOGIC ==============~~~~~

moving_avgs = {
    "GOOG": {"value": 0, "count": 0},
    "MSFT": {"value": 0, "count": 0},
    "AAPL": {"value": 0, "count": 0}
}


def update_data(exchange, update):
    global moving_avgs

    fudge = 0

    if update['type'] != 'book':
        return
    if update['symbol'] not in ["GOOG", "MSFT", "AAPL"]:
        return

    symbol = update["symbol"]

    # update midpoint averages
    if len(update['sell']) > 0 and len(update['buy']) > 0:
        old_avg = moving_avgs[symbol]["value"]
        old_cnt = moving_avgs[symbol]["count"]
        new_price = update['buy'][0][0] + (update['sell'][0][0] - update['buy'][0][0]) / 2
        moving_avgs[symbol]["value"] = old_avg * old_cnt / (old_cnt + 1) + (new_price / (old_cnt + 1))
        moving_avgs[symbol]["count"] = moving_avgs[symbol]["count"] + 1

    # preform trades
    if len(update["sell"]) > 0 and update["sell"][0][0] < moving_avgs[symbol]["value"]:
        write_to_exchange(exchange, {
            "type": "add", "order_id": 10, "symbol": symbol,
            "dir": "BUY", "price": update["sell"][0][0], "size": update["sell"][0][1]
        })
    elif len(update["buy"]) > 0 and update["buy"][0][0] > moving_avgs[symbol]["value"]:
        write_to_exchange(exchange, {
            "type": "add", "order_id": 10, "symbol": symbol,
            "dir": "SELL", "price": update["buy"][0][0], "size": update["buy"][0][1]
        })


# ~~~~~============== MAIN LOOP ==============~~~~~
def main():
    exchange = connect()

    # Hello
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    exchange_reply = read_from_exchange(exchange)
    print("The exchange replied:", exchange_reply, file=sys.stderr)

    while True:

        exchange_reply = read_from_exchange(exchange)
        update_data(exchange, exchange_reply)


if __name__ == "__main__":
    main()
