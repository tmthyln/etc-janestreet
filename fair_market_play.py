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

# round resets every 5 mins, so don't need to reset moving avg
moving_avgs = {
    "GOOG": { "value": 0, "count": 0 },
    "MSFT": { "value": 0, "count": 0 },
    "AAPL": { "value": 0, "count": 0 }
}

bought = { "GOOG": 0, "MSFT": 0, "AAPL": 0 }
order_hist = {}
curr_order = 0

def new_order(ord_type, ticker):
    curr_order = curr_order + 1
    order_hist[curr_order] = { "type": ord_type, "ticker": ticker }
    return curr_order

def trade(exchange, update):

    """
    Improvements:
    1. never be negative in a company (negative shares)
    """

    # NO MORE NEGATIVE HOLDINGS
    if update["type"] == "ack":
        ord_type = order_hist[update["order_id"]]["type"]
        ticker = order_hist[update["order_id"]]["ticker"]
        if ord_type == "BUY": bought[ticker] = bought[ticker] + 1
        if ord_type == "SELL": bought[ticker] = bought[ticker] - 1

    # do trade
    if update["type"] == "book" and update["symbol"] in ["GOOG", "MSFT", "AAPL"] and len(update["buy"] + update["sell"]) > 0:

        symbol = update["symbol"]

        # calculate fair price
        weighted_total = 0
        weight_sum = 0
        for p, q in update["buy"] + update["sell"]:
            weighted_total = weighted_total + p * q
            weight_sum = weight_sum + q
        fair_price = weighted_total / weight_sum
        print(symbol, fair_price, bought[symbol])

        # execute trade
        # buy at 1 below fair market, sell at 1 above fair market - same as bond strategy
        write_to_exchange(exchange, {
            "type": "add", "order_id": new_order("BUY"), "symbol": symbol, "dir": "BUY", "price": fair_price - 1, "size": 1
        })
        if (bought[symbol] > 0):
            write_to_exchange(exchange, {
                "type": "add", "order_id": new_order("SELL"), "symbol": symbol, "dir": "SELL", "price": fair_price + 1, "size": 1
            })


    """
    # update data
    if update["type"] == "trade" and update["symbol"] in ["GOOG", "MSFT", "AAPL"]:
        symbol = update["symbol"]

        buy_this_round = 100 - moving_avgs[symbol]["buy_amt"]
        sell_this_round = 100 - moving_avgs[symbol]["sell_amt"]

        # update moving avg
        old_avg = moving_avgs[symbol]["value"]
        old_cnt = moving_avgs[symbol]["count"]
        moving_avgs[symbol]["value"] = old_avg * old_cnt / (old_cnt + 1) + (update["price"] / (old_cnt + 1))
        moving_avgs[symbol]["count"] = moving_avgs[symbol]["count"] + 1


        # buy at 1 below fair market, sell at 1 above fair market - same as bond strategy
        write_to_exchange(exchange, { "type": "add", "order_id": 10, "symbol": symbol, "dir": "BUY", "price": moving_avgs[symbol]["value"] - 1, "size": 1 })
        write_to_exchange(exchange, { "type": "add", "order_id": 12, "symbol": symbol, "dir": "SELL", "price": moving_avgs[symbol]["value"] + 1, "size": 1 })
    """

    """
        if buy_this_round > 0:
            write_to_exchange(exchange, { "type": "add", "order_id": 10, "symbol": symbol, "dir": "BUY", "price": moving_avgs[symbol]["value"] - 1, "size": 1 })
            moving_avgs[symbol]["buy_amt"] += buy_this_round
        if sell_this_round > 0:
            write_to_exchange(exchange, { "type": "add", "order_id": 12, "symbol": symbol, "dir": "SELL", "price": moving_avgs[symbol]["value"] + 1, "size": 1 })
            moving_avgs[symbol]["sell_amt"] += sell_this_round
    """

"""
def update(update):
    if update['type'] != 'fill':
        return

    if update['symbol'] not in ["GOOG", "MSFT", "AAPL"]:
        return

    if update['dir'] == 'buy':
        moving_avgs[update['symbol']]['buy_amt'] -= update['size']
    else:
        moving_avgs[update['symbol']]['sell_amt'] -= update['size']
"""

# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()

    # Hello
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    exchange_reply = read_from_exchange(exchange)
    print("The exchange replied:", exchange_reply, file=sys.stderr)

    while True:

        exchange_reply = read_from_exchange(exchange)
        trade(exchange, exchange_reply)

if __name__ == "__main__":
    main()