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
    ''' Class to represent a stock or fund '''

    __slots__ = ('ticker', 'units', 'close_prices', 'name', 'dividends', 'currency')

    def __init__(self, ticker:str, units = 0) -> None:
        self.ticker         = ticker
        self.units          = units
        self.close_prices   = None
        self.name           = None
        self.dividends      = [] # Maybe this isn't good to store in the Stock class? Cuz it's like a growing list...

        if ticker[-3:] == '.TO':
            self.currency   = 'CAD'
        else:
            self.currency   = 'USD'
    

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


    def Value(self, date=dt.datetime.now()):
        ''' Returns the value of this position at a given date '''      
        return self.units * self.close_prices['Adj Close'][date]



# --------------------------------------------------------------------------------------------------
#class PortfolioManager:
#    ''' Class for managing an investment portfolio'''
#
#    def __init__(self, cash_CAD:float = 0, cash_USD:float = 0, initial_tickers_and_units = None) -> None:
#        self.stock_list = []
#        self.cash = {'CAD': cash_CAD, 'USD': cash_USD}
#
#        # Initialize any stocks in the portfolio.
#        # These should be passed as a numpy array with
#        # elements [..., [ticker, units], ...]
#        if initial_tickers_and_units is not None:
#            for i in np.arange(len(initial_tickers_and_units[:,0])):
#                ticker = initial_tickers_and_units[i, 0]
#                units = initial_tickers_and_units[i, 1]
#                self.AddStock(ticker, units)
#    
#
#    def AddStock(self, ticker, units = 0) -> None:
#        ''' Creates a new Stock object and adds it to the portfolio'''
#        self.stock_list.append(Stock(ticker, units))
#        return
#    
#
#    def GetStock(self, ticker) -> Stock:
#        ''' Return the stock object with the ticker specified from the portfolio stock list '''
#        stock = next((stock for stock in self.stock_list if stock.ticker == ticker), None)
#        if stock == None:
#            raise Exception('Error: A stock with the ticker {} was not found in the stock list of this portfolio'.format(ticker))
#        return stock
#    
#
#    def Deposit(self, amount, currency = 'CAD') -> None:
#        ''' Adds cash to the portfolio from a cash deposit '''
#        self.cash[currency] += amount
#    
#
#    def Withdraw(self, amount, currency) -> None:
#        ''' Removes cash from the portfolio from a cash withdrawl '''
#        self.cash[currency] -= amount
#    
#
#    def Exchange(self, from_currency, to_currency, sell_amount, buy_amount) -> None:
#        ''' Exchanges cash between currencies '''
#        self.cash[from_currency] -= sell_amount
#        self.cash[to_currency] += buy_amount
#
#        # There are also fees associated with this. Would probably have to pass date and check exchange rate...
#    
#
#    def Buy(self, ticker, units, price_per_share, total_cost) -> None:
#        ''' Performs a buy action updating cash and the stock '''
#        stock = self.GetStock(ticker)
#        self.cash[stock.currencey] -= total_cost
#        stock.Buy(units)
#
#        fee = total_cost - (units * price_per_share) # Not sure how to make use of this yet lol
#    
#
#    def Sell(self, ticker, units, price_per_share, total_gain) -> None:
#        ''' Performs a sell action updating cash and the stock'''
#        stock = self.GetStock(ticker)
#        self.cash[stock.currencey] += total_gain
#        stock.Buy(units)
#
#        fee = (units * price_per_share) - total_gain # Not sure how to make use of this yet lol
#    
#
#    def Dividend(self, amount, ticker, date) -> None:
#        ''' Adds cash from a dividend to the portfolio '''
#        stock = self.GetStock(ticker)
#        self.cash[stock.currency] = self.cash[stock.currency] + amount # This won't work for old Wealthsimple dividends!!!
#        stock.RecordDividend(amount, date)


# --------------------------------------------------------------------------------------------------
class Transaction:
    ''' Class for storing data regarding a transaction '''

    __slots__ = ('date', 'ticker', 'type', 'units', 'price_per_share', 'total_currency', 'total_amount')

    def __init__(self, date, ticker, transaction_type, units, price_per_share, total_currency, total_amount) -> None:
        self.date               = date
        self.ticker             = ticker
        self.type               = transaction_type
        self.units              = units
        self.price_per_share    = price_per_share
        self.total_currency     = total_currency
        self.total_amount       = total_amount



# --------------------------------------------------------------------------------------------------
class TransactionReader:
    ''' Class for parsing investing history tsv file '''

    def __init__(self, transaction_file) -> None:
        transaction_data = np.genfromtxt(transaction_file, delimiter='\t', skip_header=2, autostrip=True, dtype=str)

        self.dates              = np.array([dt.datetime.strptime(date, '%m/%d/%Y') for date in transaction_data[:,0]])
        self.tickers            = np.array([ticker[4:] + '.TO' if ticker[0:3] == 'TSE' else ticker for ticker in transaction_data[:,1]])
        self.actions            = np.array(action.replace(' ', '') for action in [transaction_data[:,4]])
        self.units              = np.array([float(units.replace(',','')) for units in transaction_data[:,5]])
        self.price_per_shares   = np.array([float(pps.replace(',','')) for pps in transaction_data[:,7]])
        self.total_currencies   = transaction_data[:,8]
        self.total_amounts      = np.array([float(total.replace(',','')) for total in transaction_data[:,9]])

        del transaction_data

    
    def GenerateTransactionList(self):
        ''' Method for generating a dictionary of Transaction objects from the data that was read in '''
        transactions = dict.fromkeys(self.dates, [])
        for i in np.arange(len(self.dates)):
            transactions[self.dates[i]].append(Transaction(self.dates[i], self.tickers[i], self.actions[i], self.units[i],
                                                            self.price_per_shares[i], self.total_currencies[i], self.total_amounts[i]))
        
        return transactions



# --------------------------------------------------------------------------------------------------
class Portfolio:
    ''' Class for tracking an investment portfolio '''

    def __init__(self, initial_cash_CAD:float=0., initial_cash_USD:float=0., initial_tickers_and_units = None) -> None:
        self.stock_list     = []
        self.cash           = {'CAD': initial_cash_CAD,
                                'USD': initial_cash_USD}
        
        self.value_history  = None
        self.return_history = None
        self.dates          = None

        # Initialize any stocks in the portfolio.
        # These should be passed as a numpy array with
        # elements [..., [ticker, units], ...]
        if initial_tickers_and_units is not None:
            for i in np.arange(len(initial_tickers_and_units[:,0])):
                ticker = initial_tickers_and_units[i, 0]
                units = initial_tickers_and_units[i, 1]
                self.AddStock(ticker, units)
        
        #self.my_manager = PortfolioManager()
        self.exchange_rates = pdr.get_data_yahoo('USDCAD=X', dt.datetime(2019,1,1), dt.datetime.now(), progress=False).iloc[:, [4]]
    

    # ------------------------------------------------------------------------
    # Methdos for managing the portfolio
    # ------------------------------------------------------------------------


    def AddStock(self, ticker, units = 0) -> None:
        ''' Creates a new Stock object and adds it to the portfolio '''
        self.stock_list.append(Stock(ticker, units))
    

    def RemoveStock(self, stock_to_remove) -> None:
        ''' Removes a Stock object from the stock list of the portfolio '''
        self.stock_list.remove(stock_to_remove)
    

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
    

    def FXBuy(self, amount, currency) -> None:
        ''' Processes the buy portion of a currency exchange '''
        self.cash[currency] += amount

        # There are also fees associated with this. Would probably have to pass date and check exchange rate...
    

    def FXSell(self, amount, currency) -> None:
        ''' Processes the sell portion of a currency exchange '''
        self.cash[currency] -= amount

        # There are also fees associated with this. Would probably have to pass date and check exchange rate...
    

    def Buy(self, ticker, units, price_per_share, total_cost) -> None:
        ''' Performs a buy action updating cash and the stock '''
        stock = self.GetStock(ticker)
        self.cash[stock.currencey] -= total_cost
        stock.Buy(units)

        fee = total_cost - (units * price_per_share) # Not sure how to make use of this yet lol
    

    def Sell(self, ticker, units, price_per_share, total_gain) -> None:
        ''' Performs a sell action updating cash and the stock '''
        stock = self.GetStock(ticker)
        self.cash[stock.currencey] += total_gain
        stock.Sell(units)

        fee = (units * price_per_share) - total_gain # Not sure how to make use of this yet lol

        if stock.units == 0:
            self.RemoveStock(stock)
            del stock
    

    def Dividend(self, amount, currency, ticker, date) -> None:
        ''' Adds cash from a dividend to the portfolio '''
        stock = self.GetStock(ticker)
        self.cash[currency] += amount
        stock.RecordDividend(amount, date)
    

    def Rebate(self, amount, currency='CAD') -> None:
        ''' Add cash to portfolio from a rebate '''
        self.cash[currency] += amount


    # ------------------------------------------------------------------------
    # Methods for processing transactions in the portfolio
    # ------------------------------------------------------------------------
    

    def ProcessTransaction(self, transaction) -> None:
        ''' Reads in a Transaction and applies it to the portfolio '''
        

        return


    # ------------------------------------------------------------------------
    # Methods for tracking performance
    # ------------------------------------------------------------------------
    

    def CalculateValue(self, date=dt.datetime.now()):
        ''' Calculates the value of the portfolio (in CAD) on a given date at market close '''
        exchange_rate = self.exchange_rates['Adj Close'][date]
        value = self.cash['CAD'] + (self.cash['USD'] * exchange_rate)

        for stock in self.stock_list:
            stock_value = stock.Value(date)
            if stock.currency == 'USD':
                stock_value *= exchange_rate
            value += stock_value

        return value


    def TrackValue(self, start_date, end_date) -> None:
        ''' Calculate the value of the portfolio on each day in the given time span '''
        self.dates = GetWeekdays(start_date, end_date)

        #actions = getActions
        
        # for day in dates look through actions and apply changes
        #   calculate value at close
        #   append to value list

        return

    
    def TrackReturns(self, start_date, end_date) -> None:
        # Maybe combine this with the function above? That way you know when to
        # cut on holding periods. Or just keep track of a list of holding period
        # change dates?
        # Maybe relable trackvalue to just 'Track' ?
        return



#def main() -> None:
#    return
#
#if __name__ == '__main__':
#    main()
