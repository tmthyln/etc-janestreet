"""

BABZ - BABA arbitrage

"""

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
    write_to_exchange(exchange, { "type": "add", "order_id": 10, "symbol": "BOND", "dir": "BUY", "price": 999, "size": size })
    write_to_exchange(exchange, { "type": "add", "order_id": 12, "symbol": "BOND", "dir": "SELL", "price": 1001, "size": size })

import sys

# initialize buy value to very low - i.e. market buys for low
# initialize sell value to very high - i.e. market sells for very high
main_book = {
    "BABZ": { "buy": { "price": -sys.maxint - 1, "quantity": 0 }, "sell": { "price": sys.maxint, "quantity": 0 } },
    "BABA": { "buy": { "price": -sys.maxint - 1, "quantity": 0 }, "sell": { "price": sys.maxint, "quantity": 0 } }
}

def update_book(info, book):
	if info["type"] == "book":

		symbol = info["symbol"]
		if symbol not in ["BABA", "BABZ"]: return

		if "buy" in info:
			max_buy = -sys.maxint - 1
			for order in info["buy"]:
				# get max of current set of orders
				if order[0] > max_buy:
					book[symbol]["buy"]["price"] = order[0]
					book[symbol]["buy"]["quantity"] = order[1]
					max_buy = order[0]
		if "sell" in info:
			min_sell = sys.maxint
			for order in info["sell"]:
				if order[0] < min_sell:
					book[symbol]["sell"]["price"] = order[0]
					book[symbol]["sell"]["quantity"] = order[1]
					min_sell = order[0]

def baba_arbitrage(exchange, book):

	option1quant = min(book["BABZ"]["sell"]["quantity"], book["BABA"]["buy"]["quantity"])
	option1quant = min(book["BABA"]["sell"]["quantity"], book["BABZ"]["buy"]["quantity"])

	option1 = (book["BABZ"]["sell"]["price"] - book["BABA"]["buy"]["price"]) * option1quant - 10
	option2 = (book["BABA"]["sell"]["price"] - book["BABZ"]["buy"]["price"]) * option2quant - 10

	if max(option1, option2) > 0:

		if option1 > option2:

			write_to_exchange(exchange, {
				"type": "add", "order_id": 10, "symbol": "BABZ", "dir": "BUY",
				"price": book["BABZ"]["sell"]["price"], "size": option1quant
			})

			# convert
			write_to_exchange(exchange, {
				"type": "convert", "order_id": 12, "symbol": "BABZ",
				"dir": "SELL", "size": option1quant
			})

			write_to_exchange(exchange, {
				"type": "add", "order_id": 14, "symbol": "BABA", "dir": "SELL",
				"price": book["BABA"]["buy"]["price"], "size": option1quant
			})

		else:

			write_to_exchange(exchange, {
				"type": "add", "order_id": 10, "symbol": "BABA", "dir": "BUY",
				"price": book["BABA"]["sell"]["price"], "size": option2quant
			})

			# convert
			write_to_exchange(exchange, {
				"type": "convert", "order_id": 12, "symbol": "BABZ",
				"dir": "BUY", "size": option1quant
			})

			write_to_exchange(exchange, {
				"type": "add", "order_id": 14, "symbol": "BABZ", "dir": "SELL",
				"price": book["BABZ"]["buy"]["price"], "size": option2quant
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
        # print("The exchange replied:", exchange_reply, file=sys.stderr)

        # continuous stock strat
        update_book(exchange_reply, main_book)
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
