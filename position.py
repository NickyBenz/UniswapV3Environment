from swap import Swap

class Position:
    def __init__(self,lower_price: int, upper_price: int, curr_price: int, amount0: int, amount1: int):
        if (curr_price > lower_price and curr_price < upper_price):
            in_range = True
        if (in_range):
            self.lower_price = (lower_price)
            self.upper_price = (upper_price)
            self.amount0 = amount0
            self.amount1 = amount1
        else:
            if (lower_price > curr_price):
                self.amount0 = amount0
                self.amount1 = 0
            else:
                self.amount1 = amount1
                self.amount0 = 0
        self.Q96 = 2**96

    def liquidity1(self, pc: int, pa: int, amount1: int):
        delta_price = pc - pa
        L_y = amount1 / delta_price
        return L_y

    def liquidity0(self, pc: int, pb: int, amount0: int):
        numerator = amount0 * ((pc) * (pb) * self.Q96)
        denominator = (pb) - (pc)
        L_x = numerator / denominator
        return L_x

    def getPositionLiquidity(self):
        L_x = self.liquidity0(self.curr_price, self.upper_price)
        L_y =self.liquidity1(self.curr_price, self.lower_price)
        self.position_liq = max(L_x, L_y)

    def getFeesFromSwap(self, swap: Swap, poolFeeTier: float):
        if swap.price_moved > self.upper_price or swap.price_moved < self.lower_price:
            return 0

        if swap.amount0 > 0:
            amountIn = self.amount0 * self.curr_price
        else:
            amountIn = self.amount1
        total_liquidity = swap.liquidity + self.liquidity

        liquidityShare = self.liquidity / (total_liquidity)

        return poolFeeTier * liquidityShare * amountIn

    def getImpermanentLoss(self, price_init: int, price_moved: int, external_asset_factor_change: float):
        p_c = price_init
        p_k = price_moved
        p_a = self.lower_price
        p_b = self.upper_price
        k = external_asset_factor_change

        L = self.get_position_liquidity()

        v_0 = 2 * p_c * L - (p_a - (p_c) / (p_b)) * L

        v_1 = 2 * p_k * L - (p_a - (p_k) / (p_b)) * L

        v_held = (1 + k) * (p_c) * L - (p_a + (p_c * k) / (p_b)) * L

        return ((v_1 - v_held) / (v_held) * self.amount1)

