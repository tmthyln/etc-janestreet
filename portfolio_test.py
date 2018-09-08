### DOESNT WORK

import sys

# initialize buy value to very low - i.e. market buys for low
# initialize sell value to very high - i.e. market sells for very high
main_book = {
    "GOOG": { "buy": { "price": sys.minint, "quantity": 0 } "sell": { "price": sys.maxint, "quantity": 0 } },
    "MSFT": { "buy": { "price": sys.minint, "quantity": 0 } "sell": { "price": sys.maxint, "quantity": 0 } },
    "AAPL": { "buy": { "price": sys.minint, "quantity": 0 } "sell": { "price": sys.maxint, "quantity": 0 } },
}

def update_book(info, book):
	if book["type"] == "book":

		symbol = book["symbol"]

		# sell - get lowest selling price on our book
		for order in book["sell"]:
			if book["sell"][0] < main_book[symbol]["sell"]["price"]:
				main_book[symbol]["sell"]["price"] = book["sell"][0]
				main_book[symbol]["sell"]["quantity"] = book["sell"][1]

		# buy - get highest buy price on our book
		for order in book["buy"]:
			if book["buy"][0] > main_book[symbol]["buy"]["price"]:
				main_book[symbol]["buy"]["price"] = book["buy"][0]
				main_book[symbol]["buy"]["quantity"] = book["buy"][1]

def portfolio_balance(exchange, portfolio, book):
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
