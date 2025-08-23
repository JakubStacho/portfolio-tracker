import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf

from utils.Stock import Stock
from utils.Transactions import Transactions



class Portfolio:
    '''
    Class portfolio tracking and operations
    '''
    def __init__(self, transaction_file, start_date, end_date, initial_cash_cad = 0.,
                 initial_cash_usd = 0., initial_shares = None):
        
        self.start_date = start_date
        self.end_date   = end_date

        self.transactions = Transactions(transaction_file)

        tickers_to_pull = self.transactions.df['security'].unique().tolist()
        tickers_to_pull.remove('Cash')

        # dataframe of daily stock prices
        self.price_data = yf.download(tickers_to_pull, start=start_date, end=end_date, auto_adjust=False, progress=True)['Close']
        self.price_data = self.price_data.ffill()

        # dataframe of daily portfolio positions (shares of each stock)
        self.position_data         = self.price_data.copy()
        self.position_data.iloc[:] = 0

        # dataframe of general portfolio summary
        self.portfolio_data = yf.download('CAD=X', start=start_date, end=end_date, progress=True)['Close']
        self.portfolio_data.loc[:, ['CASH-CAD', 'CASH-USD', 'deposits', 'cash', 'positions', 'value']] = 0.

        # pull data for individual stocks for adjustments (currency and stock splits)
        self.currency_data, self.split_adjuster = self.collect_stock_info(tickers_to_pull)

        # adjust daily price data for currency (convert all to CAD)
        for ticker in self.currency_data.keys():
            if self.currency_data[ticker] == 'USD':
                self.price_data[ticker] = self.price_data[ticker] * self.portfolio_data['CAD=X']


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


    # ---------------------------------------------------------
    # Methods for handling transactions in the portfolio
    # ---------------------------------------------------------
    def deposit(self, transaction):
        '''
        Process a deposit by adding cash to the portfolio and
        updating daily deposit history
        '''
        print('processing deposit')
        print(transaction)

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
        print('processing buy')
        print(transaction)
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
        print('processing fxbuy')
        print(transaction)
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
        print('processing dividend')
        print(transaction)
        # update all cash positions going forward from this date
        self.portfolio_data.loc[self.portfolio_data.index >= transaction.date, 'CASH-' + transaction.currency] += transaction.total
    

    def rebate(self, transaction):
        '''
        Process a rebate by adding cash to the portfolio
        '''
        print('processing rebate')
        print(transaction)
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
        for i, transaction in self.transactions.df[self.transactions.df['date'].between(self.start_date, self.end_date)].iterrows():
            self.process_transaction(transaction)
        
        self.portfolio_data['positions'] = (self.position_data * self.price_data).sum(axis=1)
        self.portfolio_data['cash']      = self.portfolio_data['CASH-CAD'] + self.portfolio_data['CASH-USD'] * self.portfolio_data['CAD=X']
        self.portfolio_data['value']     = self.portfolio_data['cash'] + self.portfolio_data['positions']


        
    # ------------------------------------------------------------------------
    # Methdos for managing the portfolio
    # ------------------------------------------------------------------------

    def AddTransactions(self, file_path):
        ''' Add a path to the file containing a history of investment transactions (.tsv format) '''
        self.transaction_file = file_path


    def AddStock(self, ticker, units=0) -> None:
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
    

    def StockOwned(self, ticker) -> bool:
        ''' Method checks to see whether a stock with a given ticker is in the current stock list '''
        stock = next((stock for stock in self.stock_list if stock.ticker == ticker), None)
        if stock == None:
            return False
        else:
            return True


    # ------------------------------------------------------------------------
    # Methods for processing transactions in the portfolio
    # ------------------------------------------------------------------------
    

    def ProcessTransaction(self, transaction, i) -> None:
        ''' Reads in a Transaction and applies it to the portfolio '''
        managing_function = getattr(self, transaction.type)
        managing_function(transaction, i)


    def Deposit(self, transaction, i) -> None:
        ''' Adds cash to the portfolio from a cash deposit '''
        self.cash[transaction.currency] += transaction.amount
        self.daily_deposit += transaction.amount
    

    def Withdraw(self, transaction, i) -> None:
        ''' Removes cash from the portfolio from a cash withdrawl '''
        self.cash[transaction.currency] -= transaction.amount
        self.daily_deposit -= transaction.amount
    

    def FXBuy(self, transaction, i) -> None:
        ''' Processes the buy portion of a currency exchange '''
        self.cash[transaction.currency] += transaction.amount

        # There are also fees associated with this. Would probably have to pass date and check exchange rate...
    

    def FXSell(self, transaction, i) -> None:
        ''' Processes the sell portion of a currency exchange '''
        self.cash[transaction.currency] -= transaction.amount

        # There are also fees associated with this. Would probably have to pass date and check exchange rate...
    

    def Buy(self, transaction, i) -> None:
        ''' Performs a buy action updating cash and the stock '''
        new_stock = False
        if not self.StockOwned(transaction.ticker):
            self.AddStock(transaction.ticker)
            new_stock = True

        stock = self.GetStock(transaction.ticker)
        if new_stock:
            stock.PullData(transaction.date, dt.datetime.today())
        self.cash[transaction.currency] -= transaction.amount
        stock.Buy(transaction.units)

        #fee = transaction.amount - (transaction.units * transaction.pps) # Not sure how to make use of this yet lol
    

    def Sell(self, transaction, i) -> None:
        ''' Performs a sell action updating cash and the stock '''
        stock = self.GetStock(transaction.ticker)
        self.cash[transaction.currency] += transaction.amount
        stock.Sell(transaction.units)

        #fee = (transaction.units * transaction.pps) - transaction.amount # Not sure how to make use of this yet lol

        if stock.units == 0:
            self.RemoveStock(stock)
            del stock
    

    def Dividend(self, transaction, i) -> None:
        ''' Adds cash from a dividend to the portfolio '''
        self.cash[transaction.currency] += transaction.amount
        if transaction.currency == 'USD':
            exchange_rate = self.exchange_rates[transaction.date]
        else:
            exchange_rate = 1
        self.dividend_history[i] += exchange_rate * transaction.amount
        #stock = self.GetStock(transaction.ticker)
        #stock.RecordDividend(transaction.amount, transaction.date) # I'll have to think about this later
    

    def Rebate(self, transaction, i) -> None:
        ''' Add cash to portfolio from a rebate '''
        self.cash[transaction.currency] += transaction.amount * transaction.units


    # ------------------------------------------------------------------------
    # Methods for tracking performance
    # ------------------------------------------------------------------------
    

    def CalculateValue(self, date=dt.datetime.today()):
        ''' Calculates the value of the portfolio (in CAD) on a given date at market close '''
        while date not in self.exchange_rates.keys():
            date -= dt.timedelta(days=1)
            
        exchange_rate = self.exchange_rates[date]
        value = self.cash['CAD'] + (self.cash['USD'] * exchange_rate)

        for stock in self.stock_list:
            stock_value = stock.Value(date)
            if stock.currency == 'USD':
                stock_value *= exchange_rate
            value += stock_value

        return value


    def TimeWeightedReturn(self, start_date, end_date):
        ''' Returns the time weighted rate of return series in a specified date range '''
        if start_date < self.dates[0]:
            print(start_date)
            print(self.dates[0])
            raise Exception('Error: Start date spcified lies outside of your portfolio tracking range.')
        if end_date > self.dates[-1]:
            print(end_date)
            print(self.dates[-1])
            raise Exception('Error: End date spcified lies outside of your portfolio tracking range.')
        
        while start_date not in self.dates:
            start_date += dt.timedelta(days=1)
        while end_date not in self.dates:
            end_date -= dt.timedelta(days=1)
        
        start_index = np.where(self.dates == start_date)[0][0]
        end_index   = np.where(self.dates == end_date)[0][0]

        future_value = self.value_history[start_index:end_index+1]
        present_value_with_all_cashflows = (self.value_history[start_index] - self.cumulative_deposits[start_index]
                                            + self.cumulative_deposits[start_index:end_index+1])
        return 100 * ((future_value / present_value_with_all_cashflows) - 1)


    def TrackValue(self, start_date, end_date) -> None:
        ''' Calculate the value of the portfolio on each day in the given time span '''
        self.dates            = GetWeekdays(start_date, end_date)
        days_in_range         = len(self.dates)

        self.value_history    = np.zeros(days_in_range)
        self.deposit_history  = np.zeros(days_in_range)
        self.dividend_history = np.zeros(days_in_range)
        #self.return_history   = np.zeros(days_in_range)

        self.cumulative_deposits = None

        for stock in self.stock_list:
            stock.PullData(start_date, end_date)

        reader = TransactionReader(self.transaction_file)
        transactions = reader.GenerateTransactionList()

        #print('Starting transaction processing')
        for i, date in enumerate(self.dates):
            #print('Processing portfolio value on date: ' + str(date))
            self.daily_deposit = 0
            daily_transactions = []
            try:
                daily_transactions = transactions[date]
            except:
                pass

            for transaction in daily_transactions:
                #print('Processing ' + transaction.type + ' transaction on ' + transaction.ticker)
                self.ProcessTransaction(transaction, i)
            
            portfolio_value = self.CalculateValue(date)

            self.value_history[i]   = portfolio_value
            self.deposit_history[i] = self.daily_deposit

            ## Calculate daily return based on the last known portfolio value
            #if i == 0:
            #    last_value_plus_deposits = 0
            #else:
            #    last_value_plus_deposits = self.value_history[i-1] + self.daily_deposit
            #self.return_history[i]  = HoldingPeriodReturn(last_value_plus_deposits, portfolio_value)
        
        # After getting data for all the days in the time range, calculate a few
        # more useful portfolio properties
        self.cumulative_deposits = np.cumsum(self.deposit_history)

        #value_minus_deposits = self.value_history - self.cumulative_deposits
        #self.time_weighted_ror = 100 * value_minus_deposits / self.cumulative_deposits
        self.time_weighted_ror = self.TimeWeightedReturn(start_date, end_date)