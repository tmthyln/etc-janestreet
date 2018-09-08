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

def bond_strategy(exchange):
    # always buy bond for < 1000 and sell bond for > 1000
    print("BOND STRATEGY ------------------")
 
    size = 100
    write_to_exchange(exchange, { "type": "add", "order_id": 20, "symbol": "BOND", "dir": "BUY", "price": 999, "size": size })
    write_to_exchange(exchange, { "type": "add", "order_id": 22, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": size })

import sys

# initialize buy value to very low - i.e. market buys for low
# initialize sell value to very high - i.e. market sells for very high
main_book = {
    "GOOG": { "buy": { "price": -sys.maxint - 1, "quantity": 0 }, "sell": { "price": sys.maxint, "quantity": 0 } },
    "MSFT": { "buy": { "price": -sys.maxint - 1, "quantity": 0 }, "sell": { "price": sys.maxint, "quantity": 0 } },
    "AAPL": { "buy": { "price": -sys.maxint - 1, "quantity": 0 }, "sell": { "price": sys.maxint, "quantity": 0 } },
}

def update_book(info, book):
    if info["type"] == "book":

        symbol = info["symbol"]
        if not (symbol in ["GOOG", "MSFT", "AAPL"]): return

        # sell - get lowest selling price on our book
        for order in info["sell"]:
            if info["sell"][0] < book[symbol]["sell"]["price"]:
                book[symbol]["sell"]["price"] = info["sell"][0]
                book[symbol]["sell"]["quantity"] = info["sell"][1]

        # buy - get highest buy price on our book
        for order in info["buy"]:
            if info["buy"][0] > book[symbol]["buy"]["price"]:
                book[symbol]["buy"]["price"] = info["buy"][0]
                book[symbol]["buy"]["quantity"] = info["buy"][1]

def portfolio_balance(exchange, portfolio):
    # preform trades

    # GOOG
    # if someone's sell order is less than someone elses buy order, then execute
    if portfolio["GOOG"]["sell"] < portfolio["GOOG"]["buy"]:
        quantity = min(portfolio["GOOG"]["sell"]["quantity"], portfolio["GOOG"]["sell"]["quantity"])

        # buy for what market will sell
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": 10,
            "symbol": "GOOG",
            "dir": "BUY",
            "price": portfolio["GOOG"]["sell"],
            "size": quantity 
        })

        # sell for what market will buy
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": 12,
            "symbol": "GOOG",
            "dir": "SELL",
            "price": portfolio["GOOG"]["buy"],
            "size": quantity 
        })


# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()

    # Hello
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    exchange_reply = read_from_exchange(exchange)
    print("The exchange replied:", exchange_reply, file=sys.stderr)

    count = 0
    while True:

        # call bond strat once
        count = count + 1
        if count == 1:
            bond_strategy(exchange)

        exchange_reply = read_from_exchange(exchange)
        print("The exchange replied:", exchange_reply, file=sys.stderr)

        # continuous stock strat
        update_book(exchange_reply, main_book)
        portfolio_balance(exchange, main_book)
        print(main_book)

    """
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)

    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    """

if __name__ == "__main__":
    main()