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



def HoldingPeriodReturn(start_value: float, end_value: float) -> float:
    ''' Calculate percentage investment return given two values '''
    if start_value == 0:
        return 0
    else:
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
        #self.dividends      = [] # Maybe this isn't good to store in the Stock class? Cuz it's like a growing list...

        if ticker[-3:] == '.TO':
            self.currency   = 'CAD'
        else:
            self.currency   = 'USD'
            # This one changed from canadian listed to US listed so I have to revert to CAD
            # Actually, that's ok because the transaction is still in CAD and value in USD can be exchanged
            #if self.ticker == 'HDIUF':
            #    self.currency = 'CAD'
    

    def __str__(self) -> str:
        return self.ticker
    

    def __repr__(self):
        return repr(str(self.units) + ' units of ' + self.ticker)
    

    def PullName(self) -> None:
        ''' Pulling the full company name takes a long time but we can add
            the option to do that here because why not '''
        self.name = yf.Ticker(self.ticker).info['longName']
    

    def PullData(self, start_date, end_date) -> None:
        ''' Pulls the adjusted close price data for this stock '''
        start_date -=  dt.timedelta(days=7) # Pull extra days in case of market closure
        #print('Pulling data for ' + self.ticker + ' between ' + str(start_date) + ' and ' + str(end_date))
        # Basically ignore this stock. Will set value to 0 so it doesn't matter what I pull
        if self.ticker == 'PHUNW':
            self.close_prices = pdr.get_data_yahoo('MSFT', start_date, end_date, progress=False).iloc[:, 3]
        else:
            self.close_prices = pdr.get_data_yahoo(self.ticker, start_date, end_date, progress=False).iloc[:, 3]
    

    def Buy(self, unit_number) -> None:
        ''' Adds held shares '''
        #print('Buying ' + str(unit_number) + ' units of ' + self.ticker)
        self.units += unit_number
    

    def Sell(self, unit_number) -> None:
        ''' Removes held shares '''
        #print('Selling ' + str(unit_number) + ' units of ' + self.ticker)
        self.units += unit_number
        # Should change the recording method and then update this to a -=. I temporarily set it to += now because selling is
        # in my dataset with negative units already.
    

    ''' This doesn't work for when you get a dividend after you have shold all your shares and the stock is no longer in the list '''
    #def RecordDividend(self, date, amount) -> None:
    #    ''' Records a dividend to the dividend history for this stock '''
    #    self.dividends.append([date, amount])


    def Value(self, date=dt.datetime.now()):
        ''' Returns the value of this position at a given date '''
        #print('Calculating value of ' + self.ticker + ' on the date: ' + str(date))
        while date not in self.close_prices.keys():
            date -= dt.timedelta(days=1)
        if self.ticker == 'PHUNW':
            return 0
        else:
            return self.units * self.close_prices[date]



# --------------------------------------------------------------------------------------------------
class Transaction:
    ''' Class for storing data regarding a transaction '''

    __slots__ = ('date', 'ticker', 'type', 'units', 'pps', 'currency', 'amount')

    def __init__(self, date, ticker, transaction_type, units, price_per_share, total_currency, total_amount) -> None:
        self.date       = date
        self.ticker     = ticker
        self.type       = transaction_type
        self.units      = units
        self.pps        = price_per_share
        self.currency   = total_currency
        self.amount     = total_amount
    

    def __repr__(self):
        return repr(self.ticker + ' ' + self.type + ' transaction on ' + str(self.date))



# --------------------------------------------------------------------------------------------------
class TransactionReader:
    ''' Class for parsing investing history tsv file '''

    def __init__(self, transaction_file) -> None:
        transaction_data = np.genfromtxt(transaction_file, delimiter='\t', skip_header=2, autostrip=True, dtype=str)

        self.dates              = np.array([dt.datetime.strptime(date, '%m/%d/%Y') for date in transaction_data[:,0]])
        self.tickers            = np.array([ticker[4:] + '.TO' if ticker[0:3] == 'TSE' else ticker for ticker in transaction_data[:,1]])
        self.actions            = np.array([action.replace(' ', '') for action in transaction_data[:,4]])
        self.units              = np.array([float(units.replace(',','')) for units in transaction_data[:,5]])
        self.price_per_shares   = np.array([float(pps.replace(',','')[1:]) for pps in transaction_data[:,7]])
        self.total_currencies   = transaction_data[:,8]
        self.total_amounts      = np.array([float(total.replace(',','')[1:]) for total in transaction_data[:,9]])

        # Shift any dates on weekends to the first weekday after the weekend
        for i, date in enumerate(self.dates):
            new_date = date
            while new_date.weekday() > 4:
                new_date += dt.timedelta(days=1)
            self.dates[i] = new_date

        del transaction_data

        #print(self.dates)
        #print(self.dates[0])
        #print(self.tickers[0])
        #print(self.actions[0])
        #print(self.units[0])
        #print(self.price_per_shares[0])
        #print(self.total_currencies[0])
        #print(self.total_amounts[0])
    

    def GenerateTransactionList(self):
        ''' Method for generating a dictionary of Transaction objects from the data that was read in '''
        transactions = {date: [] for date in self.dates}
        for i, date in enumerate(self.dates):
            transactions[date].append(Transaction(date, self.tickers[i], self.actions[i], self.units[i], self.price_per_shares[i], self.total_currencies[i], self.total_amounts[i]))
        
        return transactions



# --------------------------------------------------------------------------------------------------
class Portfolio:
    ''' Class for tracking an investment portfolio '''

    def __init__(self, initial_cash_CAD:float=0., initial_cash_USD:float=0., initial_tickers_and_units=None) -> None:
        self.transaction_file = None
        self.stock_list     = []
        self.cash           = {'CAD': initial_cash_CAD,
                                'USD': initial_cash_USD}
        
        self.daily_deposit    = 0
        self.deposit_history  = None
        self.value_history    = None
        self.dividend_history = None
        self.return_history   = None
        self.dates            = None

        # Initialize any stocks in the portfolio.
        # These should be passed as a numpy array with
        # elements [..., [ticker, units], ...]
        if initial_tickers_and_units is not None:
            for i in np.arange(len(initial_tickers_and_units[:,0])):
                ticker = initial_tickers_and_units[i, 0]
                units = initial_tickers_and_units[i, 1]
                self.AddStock(ticker, units)
        
        self.exchange_rates = pdr.get_data_yahoo('USDCAD=X', dt.datetime(2020,1,1), dt.datetime.now(), progress=False).iloc[:, 4]
    

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
            stock.PullData(transaction.date, dt.datetime.now())
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
        self.cash[transaction.currency] += transaction.amount


    # ------------------------------------------------------------------------
    # Methods for tracking performance
    # ------------------------------------------------------------------------
    

    def CalculateValue(self, date=dt.datetime.now()):
        ''' Calculates the value of the portfolio (in CAD) on a given date at market close '''
        exchange_rate = self.exchange_rates[date]
        value = self.cash['CAD'] + (self.cash['USD'] * exchange_rate)

        for stock in self.stock_list:
            stock_value = stock.Value(date)
            if stock.currency == 'USD':
                stock_value *= exchange_rate
            value += stock_value

        return value


    def TrackValue(self, start_date, end_date) -> None:
        ''' Calculate the value of the portfolio on each day in the given time span '''
        self.dates            = GetWeekdays(start_date, end_date)
        days_in_range         = len(self.dates)

        self.value_history    = np.zeros(days_in_range)
        self.deposit_history  = np.zeros(days_in_range)
        self.dividend_history = np.zeros(days_in_range)
        self.return_history   = np.zeros(days_in_range)

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

            # Calculate daily return based on the last known portfolio value
            if i == 0:
                last_value_plus_deposits = 0
            else:
                last_value_plus_deposits = self.value_history[i-1] + self.daily_deposit
            self.return_history[i]  = HoldingPeriodReturn(last_value_plus_deposits, portfolio_value)
        
        self.cumulative_deposits = np.cumsum(self.deposit_history)

    
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
