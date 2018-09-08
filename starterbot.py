#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="SEEKINGALPHA"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False

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


# ~~~~~============== BOND TRADING LOGIC ==============~~~~~
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

    # print(bond_buy_size, bond_sell_size)

# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
    exchange = connect()

    # Hello
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    time.sleep(1) # wait a bit for the ack hello before running
    exchange_reply = read_from_exchange(exchange)
    #print("The exchange replied:", exchange_reply, file=sys.stderr)

    while True:
        # strategies to run
        bond_strategy(exchange)

        # reply from server
        exchange_reply = read_from_exchange(exchange)
        #print("The exchange replied:", exchange_reply, file=sys.stderr)

        # update strategies
        bond_update(exchange_reply)

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