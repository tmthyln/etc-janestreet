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

# record 20 most recent prices for each to calculate means
history = {
    "BABZ": { "buy": [], "sell": [] },
    "BABA": { "buy": [], "sell": [] }
}
# our positions
positions = {
    
}

def track(exchange, update):

    # real time market requests
    if update["type"] == "book" and update["symbol"] in ["BABZ", "BABA"]:

        symbol = update["symbol"]
        n_buy = len(update["buy"])
        n_sell = len(update["sell"])

        # add new values to end
        history[symbol]["buy"].extend([p for p,q in update["buy"]])
        history[symbol]["sell"].extend([p for p,q in update["sell"]])

        # keep only 20 most recent
        history[symbol]["buy"] = history[symbol]["buy"][:-20]
        history[symbol]["sell"] = history[symbol]["sell"][:-20]

        print(n_buy, n_sell)
        print(len(history[symbol]))

# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()

    # Hello
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    exchange_reply = read_from_exchange(exchange)
    print("The exchange replied:", exchange_reply, file=sys.stderr)

    while True:

        exchange_reply = read_from_exchange(exchange)
        track(exchange, exchange_reply)

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