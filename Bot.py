import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import json
from datetime import datetime


def fetch_live_data(exchange, symbol="BTC/USDT", timeframe="1m", limit=100):
    """Fetch live OHLCV data."""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def calculate_rsi(df, window=14):
    """Calculate RSI."""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def generate_rsi_signals_partial_trades(df, rsi_buy=30, rsi_sell=70):
    """Generate RSI signals."""
    df["signal"] = 0
    if df.iloc[-1]["RSI"] < rsi_buy:
        df.iloc[-1, df.columns.get_loc("signal")] = 1  # Buy signal
    elif df.iloc[-1]["RSI"] > rsi_sell:
        df.iloc[-1, df.columns.get_loc("signal")] = -1  # Sell signal
    return df


def place_order(exchange, symbol, order_type, side, amount):
    """Place an order using Binance API."""
    try:
        if order_type == "market":
            order = exchange.create_market_order(symbol, side, amount)
        else:
            raise ValueError("Only market orders are supported in this implementation.")
        print(f"Order placed: {order}")
        return order
    except Exception as e:
        print(f"Error placing order: {e}")
        return None


def live_trading():
    """Run the trading bot continuously."""
    # Configure Binance exchange
    with open("config.json", "r") as f:
        config = json.load(f)
    api_key = config["api_key"]
    secret_key = config["secret_key"]

    exchange = ccxt.binance({
        "apiKey": api_key,
        "secret": secret_key,
    })

    # Parameters
    symbol = "BTC/USDT"
    timeframe = "1m"
    buy_percentage = 1
    sell_percentage = 1
    rsi_buy = 30
    rsi_sell = 70
    usd_balance = 48  # Starting balance in USD
    btc_position = 0  # Starting BTC position

    print("Starting live trading bot...")

    while True:
        try:
            # Step 1: Fetch live data
            data = fetch_live_data(exchange, symbol, timeframe)
            data = calculate_rsi(data)

            # Step 2: Generate signals
            data = generate_rsi_signals_partial_trades(data, rsi_buy, rsi_sell)
            signal = data.iloc[-1]["signal"]
            price = data.iloc[-1]["close"]

            # Step 3: Execute trades
            if signal == 1 and usd_balance > 0:  # Buy signal
                buy_amount_usd = usd_balance * buy_percentage
                buy_amount_btc = buy_amount_usd / price
                btc_position += buy_amount_btc
                usd_balance -= buy_amount_usd
                place_order(exchange, symbol, "market", "buy", buy_amount_btc)

            elif signal == -1 and btc_position > 0:  # Sell signal
                sell_amount_btc = btc_position * sell_percentage
                sell_amount_usd = sell_amount_btc * price
                btc_position -= sell_amount_btc
                usd_balance += sell_amount_usd
                place_order(exchange, symbol, "market", "sell", sell_amount_btc)

            # Step 4: Print portfolio status
            portfolio_value = usd_balance + (btc_position * price)
            print(f"Portfolio Value: ${portfolio_value:.2f} | USD Balance: ${usd_balance:.2f} | BTC Position: {btc_position:.6f}")

            # Wait before the next iteration
            time.sleep(60)

        except Exception as e:
            print(f"Error in live trading loop: {e}")
            time.sleep(10)  # Wait and retry in case of an error


if __name__ == "__main__":
    live_trading()




