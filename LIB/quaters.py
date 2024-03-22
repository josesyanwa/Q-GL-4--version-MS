# Import the necessary libraries
import MetaTrader5 as mt5
import pickle
import time

# PART 1

# Function to get the current market price
def get_current_market_price(symbol):
    if not mt5.initialize():
        print("Failed to connect to MetaTrader 5 terminal.")
        return None

    try:
        if not mt5.symbol_select(symbol):
            print(f"Symbol {symbol} is not valid.")
            return None

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"Failed to get tick data for symbol {symbol}.")
            return None

        current_price = tick.bid  # Use bid price for buy orders or ask for sell orders
        return current_price
    finally:
        mt5.shutdown()

# Function to calculate the three values
def get_current_mp(symbol, increment_value):
    current_price = get_current_market_price(symbol)

    if current_price is not None:
        print(f"Current price for {symbol}: {current_price}")

        current_price = max(current_price, 0)
        mp1 = round(current_price, 1)
        mp2 = round(mp1 + increment_value, 1)
        mp3 = round(mp1 - increment_value, 1)

        return mp1, mp2, mp3
    else:
        return None

# Function to calculate half points (HP1 and HP2)
def calculate_half_points(MP1, MP2, MP3):
    HP1 = (MP1 + MP3) / 2
    HP2 = (MP1 + MP2) / 2
    return HP1, HP2

# Function to calculate quarter points (QP1, QP2, QP3, QP4)
def calculate_quarter_points(MP1, HP1, MP2, HP2, MP3):
    QP1 = (MP3 + HP1) / 2
    QP2 = (HP1 + MP1) / 2
    QP3 = (MP1 + HP2) / 2
    QP4 = (HP2 + MP2) / 2
    return QP1, QP2, QP3, QP4

# Function to calculate quarter half points (QHP1 to QHP8)
def calculate_quarter_half_points(QP1, MP3, HP1, QP2, MP1, HP2, QP3, QP4):
    QHP1 = MP3 + 0.0125
    QHP2 = QP1 + 0.0125
    QHP3 = HP1 + 0.0125
    QHP4 = QP2 + 0.0125
    QHP5 = QP3 - 0.0125
    QHP6 = QP3 + 0.0125
    QHP7 = HP2 + 0.0125
    QHP8 = QP4 + 0.0125
    return QHP1, QHP2, QHP3, QHP4, QHP5, QHP6, QHP7, QHP8

# Function to calculate overshoot and undershoot
def calculate_overshoot(symbol, values):
    return {f'Overshoot_{symbol}': [value + 0.0025 for value in values]}

def calculate_undershoot(symbol, values):
    return {f'Undershoot_{symbol}': [value - 0.0025 for value in values]}


# Function to process a currency pair
def process_currency_pair(symbol, increment_value):
    result = get_current_mp(symbol, increment_value)

    if result is not None:
        print(f"Mp1 for {symbol}:", result[0])
        print(f"Mp2 for {symbol}:", result[1])
        print(f"Mp3 for {symbol}:", result[2])

        HP1, HP2 = calculate_half_points(result[0], result[1], result[2])
        print(f"HP1 for {symbol}:", HP1)
        print(f"HP2 for {symbol}:", HP2)

        QP1, QP2, QP3, QP4 = calculate_quarter_points(result[0], HP1, result[1], HP2, result[2])
        print(f"QP1 for {symbol}:", QP1)
        print(f"QP2 for {symbol}:", QP2)
        print(f"QP3 for {symbol}:", QP3)
        print(f"QP4 for {symbol}:", QP4)

        QHP1, QHP2, QHP3, QHP4, QHP5, QHP6, QHP7, QHP8 = calculate_quarter_half_points(QP1, result[2], HP1, QP2, result[1], HP2, QP3, QP4)
        print(f"QHP1 for {symbol}:", QHP1)
        print(f"QHP2 for {symbol}:", QHP2)
        print(f"QHP3 for {symbol}:", QHP3)
        print(f"QHP4 for {symbol}:", QHP4)
        print(f"QHP5 for {symbol}:", QHP5)
        print(f"QHP6 for {symbol}:", QHP6)
        print(f"QHP7 for {symbol}:", QHP7)
        print(f"QHP8 for {symbol}:", QHP8)

        overshoot_values = calculate_overshoot(symbol, [result[2], QHP1, QP1, QHP2, HP1, QHP3, QP2, QHP4, result[0], QHP5, QP3, QHP6, HP2, QHP7, QP4, QHP8, result[1]])
        undershoot_values = calculate_undershoot(symbol, [result[2], QHP1, QP1, QHP2, HP1, QHP3, QP2, QHP4, result[0], QHP5, QP3, QHP6, HP2, QHP7, QP4, QHP8, result[1]])

        print("Overshoot values:", overshoot_values)
        print("Undershoot values:", undershoot_values)

        print("\n")

        # Modify the structure of the special_values dictionary to include the symbol
        special_values[symbol] = {
            'MP1': result[0],
            'MP2': result[1],
            'MP3': result[2],
            'HP1': HP1,
            'HP2': HP2,
            'QP1': QP1,
            'QP2': QP2,
            'QP3': QP3,
            'QP4': QP4,
            'QHP1': QHP1,
            'QHP2': QHP2,
            'QHP3': QHP3,
            'QHP4': QHP4,
            'QHP5': QHP5,
            'QHP6': QHP6,
            'QHP7': QHP7,
            'QHP8': QHP8,
            'Overshoot': calculate_overshoot(symbol, [result[2], QHP1, QP1, QHP2, HP1, QHP3, QP2, QHP4, result[0], QHP5, QP3, QHP6, HP2, QHP7, QP4, QHP8, result[1]]),
            'Undershoot': calculate_undershoot(symbol, [result[2], QHP1, QP1, QHP2, HP1, QHP3, QP2, QHP4, result[0], QHP5, QP3, QHP6, HP2, QHP7, QP4, QHP8, result[1]])
        }

        return result, HP1, HP2, QP1, QP2, QP3, QP4, QHP1, QHP2, QHP3, QHP4, QHP5, QHP6, QHP7, QHP8, overshoot_values, undershoot_values
    else:
        return None

# Example usage for each currency pair
symbol_list = [
    ("EURUSD", 0.1),
    ("AUDUSD", 0.1),
    ("AUDCAD", 0.1),
    ("NZDUSD", 0.1),
    ("USDCAD", 0.1),
    ("EURGBP", 0.1),
]

# Define empty dictionaries to store values

special_values = {
    'MP1': {},
    'MP2': {},
    'MP3': {},
    'HP1': {},
    'HP2': {},
    'QP1': {},
    'QP2': {},
    'QP3': {},
    'QP4': {},
    'QHP1': {},
    'QHP2': {},
    'QHP3': {},
    'QHP4': {},
    'QHP5': {},
    'QHP6': {},
    'QHP7': {},
    'QHP8': {},
    'Overshoot': {},
    'Undershoot': {},
}

# Infinite loop to run the code every 4 minutes
while True:
    for symbol, increment_value in symbol_list:
        result, HP1, HP2, QP1, QP2, QP3, QP4, QHP1, QHP2, QHP3, QHP4, QHP5, QHP6, QHP7, QHP8, overshoot_values, undershoot_values = process_currency_pair(symbol, increment_value)

        if result is not None:
            special_values['MP1'][symbol] = result[0]
            special_values['MP2'][symbol] = result[1]
            special_values['MP3'][symbol] = result[2]
            special_values['HP1'][symbol] = HP1
            special_values['HP2'][symbol] = HP2
            special_values['QP1'][symbol] = QP1
            special_values['QP2'][symbol] = QP2
            special_values['QP3'][symbol] = QP3
            special_values['QP4'][symbol] = QP4
            special_values['QHP1'][symbol] = QHP1
            special_values['QHP2'][symbol] = QHP2
            special_values['QHP3'][symbol] = QHP3
            special_values['QHP4'][symbol] = QHP4
            special_values['QHP5'][symbol] = QHP5
            special_values['QHP6'][symbol] = QHP6
            special_values['QHP7'][symbol] = QHP7
            special_values['QHP8'][symbol] = QHP8
            special_values['Overshoot'][symbol] = overshoot_values
            special_values['Undershoot'][symbol] = undershoot_values

    # Save special values to a file
    with open('../lib/assets/special_values.pkl', 'wb') as f:
        pickle.dump(special_values, f)

    # Wait for 4 minutes before running the loop again
    time.sleep(240)


