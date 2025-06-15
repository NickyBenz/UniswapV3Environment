class Swap:
    def __init__(self, curr_price, price_moved, amount0, amount1, curr_liquidity, timestamp,TVL):
        self.curr_price = curr_price
        self.price_moved = price_moved
        self.amount0 = amount0
        self.amount1 = amount1
        self.liquidity = curr_liquidity
        self.timestamp = timestamp
        self.TVL = TVL