import sys

main_portfolio = {
    "GOOG": { "buy": { "price": sys.maxint, "quantity": 0 } "sell": { "price": sys.minint, "quantity": 0 } },
    "MSFT": { "buy": { "price": sys.maxint, "quantity": 0 } "sell": { "price": sys.minint, "quantity": 0 } },
    "AAPL": { "buy": { "price": sys.maxint, "quantity": 0 } "sell": { "price": sys.minint, "quantity": 0 } },
}

def portfolio_balance(exchange, portfolio, book):
	# check for updates

	# preform trade

	# GOOG
	# if someone's sell order is less than someone elses buy order, then execute
	if portfolio["GOOG"]["sell"] < portfolio["GOOG"]["buy"]:
		quantity = min(portfolio["GOOG"]["sell"]["quantity"], portfolio["GOOG"]["sell"]["quantity"])
