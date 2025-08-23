import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf



class Stock:
    '''
    Class to store information on specific stocks or funds
    in the portfolio
    '''
    def __init__(self, ticker):
        self.ticker         = ticker

        # pull data about the stock
        pulled_data = yf.Ticker(self.ticker)

        pulled_info   = pulled_data.info
        self.name     = pulled_info['longName']
        self.currency = pulled_info['currency']

        # calculate a reverse cumulative stock split adjustment factor
        stock_splits          = pulled_data.splits
        self.split_adjustment = stock_splits.iloc[::-1].cumprod().iloc[::-1] # NEED TO FIGURE THIS OUT. ALSO PRICE IS ALREADY ADJUSTED FOR SPLITS SO WE CAN APPLY TO BUY SELL
    

    def __str__(self):
        return self.ticker
    
    
    # def buy_sell(self, num_shares):
    #     '''
    #     Adds or removes shares from this position based
    #     on the quantity specified in the transaction
    #     '''
    #     self.shares += num_shares