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
# our orders
order_hist = {}
curr_order = 0
def new_order(order_type, symbol, price):
    global curr_order, order_hist
    curr_order = curr_order + 1
    order_hist[curr_order] = { "type": order_type, "price": price, "symbol": symbol }
    return curr_order, price

# list of positions to convert on
need_to_process = [] # need to wait for these orders to be fulfilled
convert = [] # need to either buy or sell BABZ ==> cash out

# our positions
# just counts how many shares we are in
positions = { "BABZ": 0,"BABA": 0 }

def track(exchange, update):

    global history, order_hist

    # get updates on our order requests
    if update["type"] == "ack" and update["order_id"] in need_to_process: # successful order
        
        order_id = update["order_id"]
        symbol = order_hist[order_id]["symbol"]

        convert.append(order_id)
        need_to_process.remove(order_id)

        if order_hist[order_id]["type"] == "BUY": positions[symbol] = positions[symbol] + 1
        elif order_hist[order_id]["type"] == "SELL": positions[symbol] = positions[symbol] - 1


    # update history database with real time market requests
    if update["type"] == "book" and update["symbol"] in ["BABZ", "BABA"]:

        symbol = update["symbol"]
        n_buy = len(update["buy"])
        n_sell = len(update["sell"])

        # add new values to end
        history[symbol]["buy"].extend([p for p,q in update["buy"]])
        history[symbol]["sell"].extend([p for p,q in update["sell"]])

        # keep only 20 most recent
        history[symbol]["buy"] = history[symbol]["buy"][-20:]
        history[symbol]["sell"] = history[symbol]["sell"][-20:]

def trade(exchange):

    global history, need_to_process, convert, order_hist

    if len(history["BABZ"]["buy"]) != 20 and len(history["BABA"]["buy"]) != 20 and len(history["BABZ"]["sell"]) != 20 and len(history["BABA"]["sell"]) != 20: return

    # no more arbitrage!
    if positions["BABA"] < 8:

        # get means of BABZ, BABA buy and sell
        BABA_buy = sum(history["BABA"]["buy"]) / len(history["BABA"]["buy"])
        BABA_sell = sum(history["BABA"]["sell"]) / len(history["BABA"]["sell"])
        BABZ_buy = sum(history["BABZ"]["buy"]) / len(history["BABZ"]["buy"])
        BABZ_sell = sum(history["BABZ"]["sell"]) / len(history["BABZ"]["sell"])

        # verify differences
        #print("BABA buy: ", BABZ_sell - BABA_buy)
        #print("BABA sell: ", BABA_sell - BABZ_buy)

        # execute trades

        # initial trade to buy or sell BABA
        buy_order_id = new_order("BUY", "BABA", BABA_buy + 1)
        sell_order_id = new_order("SELL", "BABA", BABA_sell - 1)
        write_to_exchange(exchange, { 
            "type": "add", "order_id": buy_order_id, "symbol": "BABA",
            "dir": "BUY", "price": BABA_buy + 1, "size": 1 # +1 to gauruntee that someone will sell
        })
        write_to_exchange(exchange, { 
            "type": "add", "order_id": sell_order_id, "symbol": "BABA",
            "dir": "BUY", "price": BABA_sell - 1, "size": 1 # -1 to gauruntee that someone will buy
        })
        need_to_process.append(buy_order_id)
        need_to_process.append(sell_order_id)

    # while we can mess with BABZ and have BABA to convert to BABZ
    while positions["BABZ"] < 8 and len(convert) > 0:

        print("CASHING OUT")

        order_id = convert.pop()
        order_type = order_hist[order_id]["type"]
        price = order_hist[order_id]["price"]
        del order_hist[order_id]

        if order_type == "BUY": # we bought BABA, so we need to to sell BABZ and convert our BABA to BABZ
            write_to_exchange(exchange, { 
                "type": "add", "order_id": 10, "symbol": "BABZ",
                "dir": "SELL", "price": price - 1, "size": 1 # -1 to gauruntee that someone will buy
            })
        elif order_type == "SELL": # we sold BABA, so we need to buy BABZ and convert our BABA to BABZ
            write_to_exchange(exchange, { 
                "type": "add", "order_id": 10, "symbol": "BABZ",
                "dir": "BUY", "price": price + 1, "size": 1 # +1 to gauruntee that someone will sell
            })

    # end of alg ~

        


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
        trade(exchange)

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