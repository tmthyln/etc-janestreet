#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import random
from collections import deque
import time

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


# ~~~~~============== BONDS LOGIC ==============~~~~~

bond_buy_size = 0
bond_sell_size = 0

bond_id = 24000


def bond_strategy(exchange):
    # always buy bond for < 1000 and sell bond for > 1000
    global bond_buy_size, bond_sell_size, bond_id

    buy_this_round = 100 - bond_buy_size
    sell_this_round = 100 - bond_buy_size

    if buy_this_round > 0:
        write_to_exchange(exchange, { "type": "add", "order_id": bond_id, "symbol": "BOND", "dir": "BUY", "price": 999, "size": buy_this_round })
        bond_buy_size += buy_this_round
    if sell_this_round > 0:
        write_to_exchange(exchange, { "type": "add", "order_id": bond_id + 1, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": sell_this_round})
        bond_sell_size += sell_this_round

    bond_id += 2


def bond_update(update):
    global bond_buy_size, bond_sell_size

    if update['type'] != 'fill':
        return
    if update['symbol'] != 'BOND':
        return

    if update['dir'] == 'BUY':
        bond_buy_size -= update['size']
    else:
        bond_sell_size -= update['size']


# ~~~~~============== STOCKS LOGIC ==============~~~~~

# round resets every 5 mins, so don't need to reset moving avg
stocks = {
    "GOOG": {"values": deque(), "max": 0, "min": sys.maxint, "buy_amt": 0, "sell_amt": 0},
    "MSFT": {"values": deque(), "max": 0, "min": sys.maxint, "buy_amt": 0, "sell_amt": 0},
    "AAPL": {"values": deque(), "max": 0, "min": sys.maxint, "buy_amt": 0, "sell_amt": 0}
}


stocks_id = 99999
orders = deque()


def fmv_midpoint(symbol):
    return int(stocks[symbol]["min"] + (stocks[symbol]["max"] - stocks[symbol]["min"]) * 0.6)


def fme_trade(exchange, update):
    global stocks_id

    if update["type"] != 'trade':
        return
    if update['symbol'] not in ["GOOG", "MSFT", "AAPL"]:
        return

    symbol = update["symbol"]

    buy_this_round = (90 - stocks[symbol]["buy_amt"]) // 10
    sell_this_round = (90 - stocks[symbol]["sell_amt"]) // 10

    moving = True

    if moving:
        # update data
        stocks[symbol]["values"].append(update["price"])

        # maintain moving window
        if len(stocks[symbol]["values"]) > 1000:
            stocks[symbol]["values"].popleft()

        # update max/min
        stocks[symbol]["max"] = max(stocks[symbol]["values"])
        stocks[symbol]["min"] = min(stocks[symbol]["values"])
    else:
        stocks[symbol]["max"] = max(stocks[symbol]["max"], update["price"])
        stocks[symbol]["min"] = min(stocks[symbol]["min"], update["price"])

    # buy or sell as necessary
    if buy_this_round > 0 and random.random() < 1.0:
        write_to_exchange(exchange, { "type": "add", "order_id": stocks_id, "symbol": symbol, "dir": "BUY", "price": int(fmv_midpoint(symbol) - 2), "size": 1})
        orders.append(stocks_id)
        stocks[symbol]["buy_amt"] += buy_this_round
        stocks_id += 1
        print('actually bought')
        print(str(fmv_midpoint(symbol) - 2))
    if sell_this_round > 0 and random.random() < 0.5:
        write_to_exchange(exchange, { "type": "add", "order_id": stocks_id, "symbol": symbol, "dir": "SELL", "price": int(fmv_midpoint(symbol) + 2), "size": 1})
        orders.append(stocks_id)
        stocks[symbol]["sell_amt"] += sell_this_round
        stocks_id += 1
        print('actually sold')
        print(str(fmv_midpoint(symbol) + 2))

    # cancel orders more than x orders old
    for order in orders:
        if order + 15 < stocks_id:
            write_to_exchange(exchange, {'type': 'cancel', 'order_id': order})
        else:
            break


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
        bond_strategy(exchange)
        exchange_reply = read_from_exchange(exchange)
        fme_trade(exchange, exchange_reply)
        fme_update(exchange_reply)
        # print(exchange_reply)
        bond_update(exchange_reply)


if __name__ == "__main__":
    main()
