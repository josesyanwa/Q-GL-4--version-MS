# 1. IMPORT LIBRARIES
import MetaTrader5 as mt5
import time
import sys

# 2.CONNECT TO MT5
if not mt5.initialize(login=48355826, server="HFMarketsGlobal-Demo", password="t*c4zAV$"):
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# 3. CONFIGS
MAX_DIST_SL = 0.0010  # Max distance between current price and SL, otherwise SL will update
TRAIL_AMOUNT = 0.0003  # Amount by how much SL updates
DEFAULT_SL = 0.0010  # If position has no SL, set a default SL

# 4.FUNCTION TO TRAIL SL
def trail_sl(position):
    # get position data
    order_type = position.type
    price_current = position.price_current
    price_open = position.price_open
    sl = position.sl
    tp = position.tp  # Get the take profit value

    dist_from_sl = abs(round(price_current - sl, 6))

    if dist_from_sl > MAX_DIST_SL:
        # calculating new sl
        if sl != 0.0:
            if order_type == 0:  # 0 stands for BUY
                new_sl = sl + TRAIL_AMOUNT
            elif order_type == 1:  # 1 stands for SELL
                new_sl = sl - TRAIL_AMOUNT
        else:
            # setting default SL if there is no SL on the symbol
            new_sl = price_open - DEFAULT_SL if order_type == 0 else price_open + DEFAULT_SL

        # Set the take profit value if it's not zero
        new_tp = tp

        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': position.ticket,
            'sl': new_sl,
            'tp': new_tp  # Update the stop-loss without altering the take profit
        }

        result = mt5.order_send(request)
        print(result)
        return result

if __name__ == '__main__':
    print('Starting Trailing Stoploss..')

    # Strategy loop
    while True:
        positions = mt5.positions_get()
        if positions:
            for position in positions:
                result = trail_sl(position)
        # Wait 10 seconds before checking again
        time.sleep(10)
