# 1. Import necessary libraries

from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas_ta as ta
import pytz
import pickle
import pandas as pd
import time
import numpy as np 


while True:
   
   pd.set_option('display.max_columns', 500)
   pd.set_option('display.width', 1500)

   # 2. Initialize and log in to the MetaTrader 5 terminal

   print("MetaTrader5 package author: ", mt5.__author__)
   print("MetaTrader5 package version: ", mt5.__version__)

   if not mt5.initialize(login=48355826, server="HFMarketsGlobal-Demo", password="t*c4zAV$"):
       print("initialize() failed, error code =", mt5.last_error())
       quit()

   print(mt5.terminal_info())
   print(mt5.version())

   # 3. GET THE SYMBOLS I WANT TO TRADE

   symbols = mt5.symbols_get()
   print('Symbols: ', len(symbols))

   desired_symbols = ['EURUSD', 'EURCAD', 'AUDUSD', 'AUDCAD', 'NZDCAD', 'NZDUSD']

   count = 0
   for s in symbols:
       if s.name in desired_symbols:
           count += 1
           print("{}. {}".format(count, s.name))
           if count == len(desired_symbols):
               break

   print()

   # 4. SET THE TIMEFRAME TO 5 MINS

   timeframe = mt5.TIMEFRAME_M15

   # 5. GET HISTORICAL PRICE DATA

   timezone = pytz.timezone("Africa/Nairobi")
   now = datetime.now(timezone)
   start_time = now - timedelta(days=4)
   utc_start_time = start_time.astimezone(pytz.utc)

   # 6. CONVERT THE DATA TO A PANDAS DATAFRAME

   df = pd.DataFrame()

   desired_symbols = ['EURUSD', 'EURCAD', 'AUDUSD', 'NZDCAD', 'NZDUSD', 'AUDCAD']
   for symbol in desired_symbols:
       rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)


       #print(f"\nDisplay obtained data for {symbol} 'as is'")

       rates_frame = pd.DataFrame(rates)
       rates_frame['symbol'] = symbol
       rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
       df = pd.concat([df, rates_frame], ignore_index=True)


   df = df[df['symbol'].isin(desired_symbols)]
   df['time'] = pd.to_datetime(df['time'], unit='s')
   df.set_index('time', inplace=True)
   df.sort_index(inplace=True)



   

   # 8- TRADING STRATEGY


   df['previous_high'] = df['high'].shift(1)
   df['previous_low'] = df['low'].shift(1)
   df['previous_open'] = df['open'].shift(1)
   df['previous_close'] = df['close'].shift(1)

   def trading_strategy(candle):
       bull_cond1 = candle['close'] > candle['open']  # bull candle condition
       bull_cond2 = candle['close'] > candle['previous_high']  # engulfment condition
       bull_cond3 = candle['previous_open'] > candle['previous_close']  # previous candle must be a bear candle

       bear_cond1 = candle['close'] < candle['open']  # bear candle condition
       bear_cond2 = candle['close'] < candle['previous_low']  # engulfment condition
       bear_cond3 = candle['previous_open'] < candle['previous_close']  # previous candle must be a bull candle

       # special condition - engulfing candle body is 1.5 times as long as previous candle range
       if candle['previous_high'] - candle['previous_low'] == 0:
           return np.nan

       special_cond = abs(candle['open'] - candle['close']) / (candle['previous_high'] - candle['previous_low']) >= 1.5

       if bull_cond1 and bull_cond2 and bull_cond3 and special_cond :
           return 'Buy'
       elif bear_cond1 and bear_cond2 and bear_cond3 and special_cond :
           return 'Sell'
       else:
           return np.nan

   # Example usage:

   # Apply the trading strategy to each row in the DataFrame
   df['TradeSignal'] = df.apply(trading_strategy, axis=1)

   # Filter rows with trade signals
   buy_signals = df[df['TradeSignal'] == 'Buy']
   sell_signals = df[df['TradeSignal'] == 'Sell']

   print(df)

   # Print the buy and sell signals
   print("Buy Signals:")
   print(buy_signals[['symbol', 'TradeSignal']])
   print("\nSell Signals:")
   print(sell_signals[['symbol', 'TradeSignal']])



   #10 .  PLACING TRADES.


   if not mt5.initialize():
       print("initialize() failed, error code =", mt5.last_error())
       quit()

   # Separate the DataFrame into two parts based on time
   current_time = df.index[-1]  
   past_df = df[df.index < current_time]
   current_df = df[df.index >= current_time]

   # For the past part, print 'No trade' for all symbols
   for symbol in desired_symbols:
       print(f"No trade for {symbol}")

   # For the current part, place trades
   for index, row in current_df.iterrows():
       symbol = row['symbol']
       trade_signal = row['TradeSignal']

       if pd.isna(trade_signal):
           print(f"No trade for {symbol}")

           ##   FOR SELL
       
       elif trade_signal == 'Sell':
           print(f"Sell {symbol}")
           

           symbol_info = mt5.symbol_info(symbol)
           if symbol_info is None:
               print(symbol, "not found, can not call order_check()")
               continue

           if not symbol_info.visible:
               print(symbol, "is not visible, trying to switch on")
               if not mt5.symbol_select(symbol, True):
                   print("symbol_select({}) failed, exit".format(symbol))
                   continue

           lot = 0.1
           point = mt5.symbol_info(symbol).point
           price = mt5.symbol_info_tick(symbol).bid
           deviation = 20
           request = {
               "action": mt5.TRADE_ACTION_DEAL,
               "symbol": symbol,
               "volume": lot,
               "type": mt5.ORDER_TYPE_SELL,
               "price": price,
               "sl": price + 100 * point,
               "tp": price - 200 * point,
               "deviation": deviation,
               "magic": 234000,
               "comment": "python script open",
               "type_time": mt5.ORDER_TIME_GTC,
               "type_filling": mt5.ORDER_FILLING_FOK,
           }

           
           result = mt5.order_send(request)
           
           print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
           if result.retcode != mt5.TRADE_RETCODE_DONE:
               print("2. order_send failed, retcode={}".format(result.retcode))
               
               result_dict = result._asdict()
               for field in result_dict.keys():
                   print("   {}={}".format(field, result_dict[field]))
                   
                   if field == "request":
                       traderequest_dict = result_dict[field]._asdict()
                       for tradereq_filed in traderequest_dict:
                           print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
               print("shutdown() and quit")
               mt5.shutdown()
               quit()

           print("2. order_send done, ", result)
           print("   opened position with POSITION_TICKET={}".format(result.order))


           ## FOR BUY

       elif trade_signal == 'Buy':
           print(f"Buy {symbol}")
           

           symbol_info = mt5.symbol_info(symbol)
           if symbol_info is None:
               print(symbol, "not found, can not call order_check()")
               continue

           if not symbol_info.visible:
               print(symbol, "is not visible, trying to switch on")
               if not mt5.symbol_select(symbol, True):
                   print("symbol_select({}) failed, exit".format(symbol))
                   continue

           lot = 0.1
           point = mt5.symbol_info(symbol).point
           price = mt5.symbol_info_tick(symbol).ask
           deviation = 20
           request = {
               "action": mt5.TRADE_ACTION_DEAL,
               "symbol": symbol,
               "volume": lot,
               "type": mt5.ORDER_TYPE_BUY,
               "price": price,
               "sl": price - 100 * point,
               "tp": price + 200 * point,
               "deviation": deviation,
               "magic": 234000,
               "comment": "python script open",
               "type_time": mt5.ORDER_TIME_GTC,
               "type_filling": mt5.ORDER_FILLING_FOK,
           }

           
           result = mt5.order_send(request)
           
           print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
           if result.retcode != mt5.TRADE_RETCODE_DONE:
               print("2. order_send failed, retcode={}".format(result.retcode))
               
               result_dict = result._asdict()
               for field in result_dict.keys():
                   print("   {}={}".format(field, result_dict[field]))
                   
                   if field == "request":
                       traderequest_dict = result_dict[field]._asdict()
                       for tradereq_filed in traderequest_dict:
                           print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
               print("shutdown() and quit")
               mt5.shutdown()
               quit()

           print("2. order_send done, ", result)
           print("   opened position with POSITION_TICKET={}".format(result.order))

   # Shutdown MetaTrader 5 at the end
   mt5.shutdown()

   time.sleep(15 * 60)