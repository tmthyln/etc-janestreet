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
test_exchange_index=1
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

# round resets every 5 mins, so don't need to reset moving avg
stocks = {
    "GOOG": {"max": 0, "min": sys.maxint, "buy_amt": 0, "sell_amt": 0},
    "MSFT": {"max": 0, "min": sys.maxint, "buy_amt": 0, "sell_amt": 0},
    "AAPL": {"max": 0, "min": sys.maxint, "buy_amt": 0, "sell_amt": 0}
}


def fmv_midpoint(symbol):
    return stocks[symbol]["min"] + (stocks[symbol]["max"] - stocks[symbol]["min"]) / 2


def fme_trade(exchange, update):
    if update["type"] != 'trade':
        return
    if update['symbol'] not in ["GOOG", "MSFT", "AAPL"]:
        return

    # update data
    symbol = update["symbol"]

    buy_this_round = (100 - stocks[symbol]["buy_amt"]) // 6
    sell_this_round = (100 - stocks[symbol]["sell_amt"]) // 6

    # update max/min
    stocks[symbol]["max"] = max(update["price"], stocks[symbol]["max"])
    stocks[symbol]["min"] = min(update["price"], stocks[symbol]["min"])

    print(fmv_midpoint(symbol))

    if buy_this_round > 0:
        write_to_exchange(exchange, { "type": "add", "order_id": 10, "symbol": symbol, "dir": "BUY", "price": fmv_midpoint(symbol) - 2, "size": 1})
        stocks[symbol]["buy_amt"] += buy_this_round
        print('actually bought')
    if sell_this_round > 0:
        write_to_exchange(exchange, { "type": "add", "order_id": 12, "symbol": symbol, "dir": "SELL", "price": fmv_midpoint(symbol) + 2, "size": 1})
        stocks[symbol]["sell_amt"] += sell_this_round
        print('actually sold')


def fme_update(update):
    if update['type'] != 'fill':
        return

    if update['symbol'] not in ["GOOG", "MSFT", "AAPL"]:
        return

    if update['dir'] == 'buy':
        stocks[update['symbol']]['buy_amt'] -= update['size']
    else:
        stocks[update['symbol']]['sell_amt'] -= update['size']


# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()

    # Hello
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    _ = read_from_exchange(exchange)

    while True:

        exchange_reply = read_from_exchange(exchange)
        fme_trade(exchange, exchange_reply)
        fme_update(exchange_reply)
        print(exchange_reply)


if __name__ == "__main__":
    main()
