import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf

from pandas.tseries.offsets import BDay

# from utils.Transactions import Transactions



# TODO
# - implement intial values

class Portfolio:
    '''
    Class portfolio tracking and operations
    '''
    def __init__(self, transaction_file, start_date, end_date, initial_cash_cad=0.,
                 initial_cash_usd=0., initial_shares=None):
        
        self.start_date = start_date
        self.end_date   = end_date

        self.transactions = self.collect_transactions(transaction_file)

        tickers_to_pull = self.transactions['security'].unique().tolist()
        tickers_to_pull.remove('Cash')

        # dataframe of daily stock prices
        self.price_data = yf.download(tickers_to_pull, start=start_date, end=end_date, auto_adjust=False, progress=False)['Close']
        self.price_data = self.price_data.ffill()

        # dataframe of daily portfolio positions (shares of each stock)
        self.position_data         = self.price_data.copy()
        self.position_data.iloc[:] = 0

        # dataframe of general portfolio summary
        self.portfolio_data = yf.download('CAD=X', start=start_date, end=end_date, auto_adjust=True,  progress=False)['Close']
        self.portfolio_data.loc[:, ['CASH-CAD', 'CASH-USD', 'deposits', 'cash', 'positions', 'value']] = 0.

        # pull data for individual stocks for adjustments (currency and stock splits)
        self.currency_data, self.split_adjuster = self.collect_stock_info(tickers_to_pull)

        # adjust daily price data for currency (convert all to CAD)
        for ticker in self.currency_data.keys():
            if self.currency_data[ticker] == 'USD':
                self.price_data[ticker] = self.price_data[ticker] * self.portfolio_data['CAD=X']
        
        # run tracking calculations
        self.calculate_daily_value()
        self.calculate_compounding_returns()


    def collect_stock_info(self, tickers):
        '''
        Collects currency and stock split data for each ticker that
        is used to adjust prices and share count
        '''
        # dictionary for storing stock currencies
        currency_dict = {}

        # dataframe for stock split adjustment factors
        split_adjuster = self.position_data.copy()
        split_adjuster.iloc[:] = 1

        for ticker in tickers:
            pulled_data = yf.Ticker(ticker)

            currency_dict[ticker] = pulled_data.info['currency']

            stock_splits     = pulled_data.splits
            split_adjustment = stock_splits.iloc[::-1].cumprod().iloc[::-1] # reverse direction cumprod for backwards adjusting

            # remove the time from the datetime index so it can be compared to the price data
            split_adjustment.index = pd.to_datetime(split_adjustment.index).date


            split_adjuster[ticker] = split_adjustment.reindex(split_adjuster.index, method='bfill').fillna(1)
        
        return currency_dict, split_adjuster
    

    def collect_transactions(self, transaction_file):
        '''
        Collects and parses transactions csv into a dataframe
        '''
        transaction_history         = pd.read_csv(transaction_file, skiprows=1)[['date', 'security', 'action', 'quantity', 'currency', 'total']]
        transaction_history['date'] = pd.to_datetime(transaction_history['date'], format='%m/%d/%Y')

        # canadian security tickers can be formatted to start with TSE: rather than end with .TO so convert all these
        # to end with .TO
        updated_tickers = np.array([ticker[4:] + '.TO' if ticker[0:3] == 'TSE' else ticker for ticker in transaction_history['security']])
        transaction_history['security'] = updated_tickers

        # shift any date that is not a business day to the next business day
        transaction_history['date'] = transaction_history['date'] + 0 * BDay()

        return transaction_history


    # ---------------------------------------------------------
    # Methods for handling transactions in the portfolio
    # ---------------------------------------------------------
    def deposit(self, transaction):
        '''
        Process a deposit by adding cash to the portfolio and
        updating daily deposit history
        '''
        # update all cash positions going forward from this date
        self.portfolio_data.loc[self.portfolio_data.index >= transaction.date, 'CASH-' + transaction.currency] += np.sign(transaction.quantity) * transaction.total

        # update the daily deposit for the specific date
        self.portfolio_data.loc[transaction.date, 'deposits'] += np.sign(transaction.quantity) * transaction.total


    def withdraw(self, transaction):
        '''
        Process a withdraw using the deposit method
        '''
        self.deposit(transaction)


    def buy(self, transaction):
        '''
        Processes a buy action updating cash and shares
        of a position
        '''
        # update all cash positions going forward from this date
        self.portfolio_data.loc[self.portfolio_data.index >= transaction.date, 'CASH-' + transaction.currency] -= np.sign(transaction.quantity) * transaction.total

        # update all share counts going forward form this date
        split_adjustment_factor = self.split_adjuster.loc[transaction.date, transaction.security]
        self.position_data.loc[self.position_data.index >= transaction.date, transaction.security] += transaction.quantity * split_adjustment_factor
 

    def sell(self, transaction):
        '''
        Processes a sell using the buy method
        '''
        self.buy(transaction)
    

    def fxbuy(self, transaction):
        '''
        Processes the buy side of a currency exchange by updating the
        cash position associated with the currency in the portfolio
        '''
        # update all cash positions going forward from this date
        self.portfolio_data.loc[self.portfolio_data.index >= transaction.date, 'CASH-' + transaction.currency] += np.sign(transaction.quantity) * transaction.total
    

    def fxsell(self, transaction):
        '''
        Processes the sell side of a currency exchange using the fxbuy method
        '''
        self.fxbuy(transaction)
    

    def dividend(self, transaction):
        '''
        Processes a dividend by adding cash to the portfolio
        '''
        # update all cash positions going forward from this date
        self.portfolio_data.loc[self.portfolio_data.index >= transaction.date, 'CASH-' + transaction.currency] += transaction.total
    

    def rebate(self, transaction):
        '''
        Process a rebate by adding cash to the portfolio
        '''
        # update all cash positions going forward from this date
        self.portfolio_data.loc[self.portfolio_data.index >= transaction.date, 'CASH-' + transaction.currency] += np.sign(transaction.quantity) * transaction.total


    def process_transaction(self, transaction):
        '''
        Processes a given transaction by passing it on to the corresponding
        handling function
        '''
        # format the action to correspond to method names
        action = transaction.action.replace(' ','').lower()

        managing_method = getattr(self, action)
        managing_method(transaction)


    # ---------------------------------------------------------
    # Methods for calculating portfolio value and returns
    # ---------------------------------------------------------
    def calculate_daily_value(self):
        '''
        Processes all the transactions in the transaction file
        to populate the portfolio_data dataframe
        '''
        for i, transaction in self.transactions[self.transactions['date'].between(self.start_date, self.end_date)].iterrows():
            self.process_transaction(transaction)
        
        self.portfolio_data['positions'] = (self.position_data * self.price_data).sum(axis=1).ffill()
        self.portfolio_data['positions'] = self.portfolio_data['positions'].ffill() # forward fill days where both cad and us markets are closed
        self.portfolio_data['cash']      = self.portfolio_data['CASH-CAD'] + self.portfolio_data['CASH-USD'] * self.portfolio_data['CAD=X']
        self.portfolio_data['value']     = self.portfolio_data['cash'] + self.portfolio_data['positions']

    
    def calculate_compounding_returns(self):
        '''
        Calculate the compounding daily returns of the portfolio
        based on the data in portfolio_data
        '''
        self.portfolio_data['value-diff'] = self.portfolio_data['value'].diff() - self.portfolio_data['deposits']
        self.portfolio_data['pct-change'] = self.portfolio_data['value-diff'] / self.portfolio_data['value'].shift(1)
        self.portfolio_data['pct-change'] = self.portfolio_data['pct-change'].fillna(0)

        self.portfolio_data['returns'] = ((self.portfolio_data['pct-change'] + 1).cumprod() - 1) * 100.

        self.portfolio_data = self.portfolio_data.drop(['value-diff', 'pct-change'], axis=1)