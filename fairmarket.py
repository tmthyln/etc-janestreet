from utils import *


class FairMarketEvaluator:
    def __init__(self, stock: str):
        self.stock = stock

    def update(self, book_json_str):
        book = json2dict(book_json_str)

        if book['symbol'] != stock:
            return


