#!./env/bin/ python3

'''
File containing functions and objects for tracking investment returns
'''

# Import modules
import datetime as dt
import numpy as np
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf

# Need to run this for datareader to pull yahoo data correctly
yf.pdr_override()



def HoldingPeriodReturn(start_value, end_value) -> float:
    ''' Calculate percentage investment return given two values '''
    if start_value == 0:
        raise Exception('Error: Cannot use 0 as the initial value of an investment.')
    
    return (end_value / start_value) - 1


def GetWeekdays(start_date, end_date):
    ''' Returns an array of all the weekdays within the specified bounds inclusively '''
    duration = (end_date - start_date).days

    if start_date.weekday() > 4:
        print('Warning: Start date specified is a weekend. The next weekday will be used as the start date.')
    
    weekday_list = []

    for i in range(duration + 1):
        next_day = start_date + dt.timedelta(days=i)
        weekday = True if next_day.weekday() < 5 else False
        if not weekday:
            continue
        weekday_list.append(next_day)
    
    weekday_list = np.array(weekday_list)
    return weekday_list



# --------------------------------------------------------------------------------------------------
class Stock:
    ''' Class to represent a stock or fund'''

    __slots__ = ('ticker', 'units', 'close_prices', 'name', 'dividends', 'currencey')

    def __init__(self, ticker:str, units = 0) -> None:
        self.ticker = ticker
        self.units = units
        self.close_prices = None
        self.name = None
        self.dividends = [] # Maybe this isn't good to store in the Stock class? Cuz it's like a growing list...

        if ticker[-3:] == '.TO':
            self.currency = 'CAD'
        else:
            self.currency = 'USD'
    

    def __str__(self) -> str:
        return self.ticker
    

    def PullName(self) -> None:
        ''' Pulling the full company name takes a long time but we can add
            the option to do that here because why not '''
        self.name = yf.Ticker(self.ticker).info['longName']
    

    def PullData(self, start_date, end_date) -> None:
        ''' Pulls the adjusted close price data for this stock '''
        self.close_prices = pdr.get_data_yahoo(self.ticker, start_date, end_date, progress=False).iloc[:, [4]]
    

    def Buy(self, unit_number) -> None:
        ''' Adds held shares '''
        self.units += unit_number
    

    def Sell(self, unit_number) -> None:
        ''' Removes held shares '''
        self.units -= unit_number
    

    def RecordDividend(self, date, amount) -> None:
        ''' Records a dividend to the dividend history for this stock '''
        self.dividends.append([date, amount])



# --------------------------------------------------------------------------------------------------
class PortfolioManager:
    ''' Class for managing an investment portfolio'''

    def __init__(self, cash_CAD:float = 0, cash_USD:float = 0, initial_tickers_and_units = None) -> None:
        self.stock_list = []
        self.cash = {'CAD': cash_CAD, 'USD': cash_USD}

        # Initialize any stocks in the portfolio.
        # These should be passed as a numpy array with
        # elements [..., [ticker, units], ...]
        if initial_tickers_and_units is not None:
            for i in np.arange(len(initial_tickers_and_units[:,0])):
                ticker = initial_tickers_and_units[i, 0]
                units = initial_tickers_and_units[i, 1]
                self.AddStock(ticker, units)
    

    def AddStock(self, ticker, units = 0) -> None:
        ''' Creates a new Stock object and adds it to the portfolio'''
        self.stock_list.append(Stock(ticker, units))
        return
    

    def GetStock(self, ticker) -> Stock:
        ''' Return the stock object with the ticker specified from the portfolio stock list '''
        stock = next((stock for stock in self.stock_list if stock.ticker == ticker), None)
        if stock == None:
            raise Exception('Error: A stock with the ticker {} was not found in the stock list of this portfolio'.format(ticker))
        return stock
    

    def Deposit(self, amount, currency = 'CAD') -> None:
        ''' Adds cash to the portfolio from a cash deposit '''
        self.cash[currency] += amount
    

    def Withdraw(self, amount, currency) -> None:
        ''' Removes cash from the portfolio from a cash withdrawl '''
        self.cash[currency] -= amount
    

    def Exchange(self, from_currency, to_currency, sell_amount, buy_amount) -> None:
        ''' Exchanges cash between currencies '''
        self.cash[from_currency] -= sell_amount
        self.cash[to_currency] += buy_amount
    

    def Buy(self, ticker, units, price_per_share, total_cost) -> None:
        ''' Performs a buy action updating cash and the stock '''
        stock = self.GetStock(ticker)
        self.cash[stock.currencey] -= total_cost
        stock.Buy(units)

        fee = total_cost - (units * price_per_share) # Not sure how to make use of this yet lol
    

    def Sell(self, ticker, units, price_per_share, total_gain) -> None:
        ''' Performs a sell action updating cash and the stock'''
        stock = self.GetStock(ticker)
        self.cash[stock.currencey] += total_gain
        stock.Buy(units)

        fee = (units * price_per_share) - total_gain # Not sure how to make use of this yet lol
    

    def Dividend(self, amount, ticker, date) -> None:
        ''' Adds cash from a dividend to the portfolio '''
        stock = self.GetStock(ticker)
        self.cash[stock.currency] = self.cash[stock.currency] + amount # This won't work for old Wealthsimple dividends!!!
        stock.RecordDividend(amount, date)



# --------------------------------------------------------------------------------------------------
class Portfolio:
    ''' Class for tracking an investment portfolio'''

    def __init__(self, initial_cash_CAD:float = 0, initial_cash_USD:float = 0, initial_tickers_and_units = None) -> None:
        self.stock_list = []
        self.cash = {'CAD': [initial_cash_CAD],
                     'USD': [initial_cash_USD]}
        
        self.values = None
        self.dates = None

        # Initialize any stocks in the portfolio.
        # These should be passed as a numpy array with
        # elements [..., [ticker, units], ...]
        if initial_tickers_and_units is not None:
            for i in np.arange(len(initial_tickers_and_units[:,0])):
                ticker = initial_tickers_and_units[i, 0]
                units = initial_tickers_and_units[i, 1]
                self.AddStock(ticker, units)
        
    
    def CalculateValue(self, start_date, end_date) -> None:
        ''' Calculate the value of the portfolio on each day in the given time span '''
        self.dates = GetWeekdays(start_date, end_date)

        #actions = getActions
        
        # for day in dates look through actions and get value

        return

    
    def CalculateReturns(self, start_date, end_date) -> None:
        return



#def main() -> None:
#    return
#
#if __name__ == '__main__':
#    main()
