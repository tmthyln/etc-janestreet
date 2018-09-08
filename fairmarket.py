from utils import *


class FairMarketEvaluator:
    def __init__(self, stock: str):
        self.stock = stock
        self.fmv = 0

    def update(self, book_json_str):
        book = json2dict(book_json_str)

        assert book["type"] == "BOOK"

        if book['symbol'] != self.stock:
            return

        buyers = book["buy"]

        print(buyers)



if __name__ == '__main__':
    bond = FairMarketEvaluator('BOND')




