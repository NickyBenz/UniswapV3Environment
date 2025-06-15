import math
import requests

import pandas as pd

from datetime import datetime

from swap import Swap

from position import Position

def priceToSqrt(price):
    Q96 = 2**96
    return math.sqrt(price) * Q96

class V3TraderFramework:

    def __init__(self,url: str, pool_address: str, poolFeeTier: float, api_key:str):
        self.tickBase = 1.001
        self.pool_address = pool_address
        self.url = url 
        self.poolFeeTier = poolFeeTier
        self.Q96 = 2**96
        self.api_key = api_key


    def amount0(self,pc: int, pb: int, liquidity: int):
        numerator = (pb) - (pc)
        denominator = self.Q96 * (pc) * (pb)
        delta_x = numerator / denominator
        return delta_x

    def amount1(self,pc: int, pa: int, liquidity: int):
        return (pc) * (pa) * liquidity

    def priceToTick(self,price: int):
        math.log(price, self.tickBase)

    def quote(self,lower_price: int, upper_price: int, amount0: int, amount1: int):
        pos = Position(lower_price, upper_price, amount0, amount1)
        pos.get_position_liquidity()
        return pos

    def retrieveSwapsData(self,from_time: int, to_time: int, frequency=3600, batch_size=1000, ):
        current_timestamp = from_time
        swaps = []
        while True:
            query = f"""   
            {{
             swaps(first:{batch_size},where: {{pool: "{self.pool_address}", timestamp_gte: "{current_timestamp}", timestamp_lte: "{to_time}"}}) 
             {{
                    amount0
                    amount1
                    sqrtPriceX96
                    pool {{
                      liquidity
                      totalValueLockedUSD
                    }}
                    timestamp
                    
                }}
            }}
            """
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.post(url=self.url, headers=headers,json={"query": query})
            data = response.json()

            batch= data.get("data", {}).get("swaps", {})
            if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.text}")
                break
            current_timestamp += frequency
            if not batch:
                break
            swaps.append(batch)
            print(f"Total records fetched: {len(swaps)*batch_size}")

        curr_price = swaps[0][0]['sqrtPriceX96']
        swap_data = []
        swap_df_data = []
        for batch in swaps[0:]:
            for swap in batch:
                price_moved = float(swap['sqrtPriceX96'])
                amount0 = float(swap['amount0'])
                amount1 = float(swap['amount1'])
                liquidity = float(swap['pool']['liquidity'])
                timestamp = float(swap['timestamp'])
                tvl = float(swap['pool']['totalValueLockedUSD'])
                swap_object = Swap(curr_price=curr_price, price_moved=price_moved, amount0=amount0, amount1=amount1,
                                  curr_liquidity=liquidity, timestamp=timestamp, TVL=tvl)
                swap_dict = {
                    "curr_price": curr_price,
                    "price_moved": price_moved,
                    "amount0": amount0,
                    "amount1": amount1,
                    "liquidity": liquidity,
                    "timestamp": timestamp,
                    "tvl": tvl 
                }
                curr_price = price_moved
                swap_df_data.append(swap_dict)
                swap_data.append(swap_object)
        swap_df = pd.DataFrame(swap_df_data)
        return swap_data, swap_df

    def calculatePositionalPNL(self, position: Position, swaps: list[Swap], external_asset_returns: list['float']):
        timestamps = [swap.timestamp for swap in swaps]
        dates = [datetime.frometimestamp(ts) for ts in timestamps]
        feesFromSwaps = [position.getFeesFromSwap(swap, self.poolFeeTier) for swap in swaps]
        impermanentLoss = [position.getImpermanentLoss(swap.curr_price, swap.price_moved, k) for swap, k in
                           zip(swaps, external_asset_returns)]
        pnl = pd.Series([f - il for f, il in zip(feesFromSwaps, impermanentLoss)], index=dates).cumsum()
        return pnl
