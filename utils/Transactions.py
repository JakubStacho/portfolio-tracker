import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf

from pandas.tseries.offsets import BDay



class Transactions:
    '''
    Class that stores and parses transaction history data
    '''
    def __init__(self, transaction_file):
        transaction_history         = pd.read_csv(transaction_file, skiprows=1)[['date', 'security', 'action', 'quantity', 'currency', 'total']]
        transaction_history['date'] = pd.to_datetime(transaction_history['date'], format='%m/%d/%Y')

        # canadian security tickers can be formatted to start with TSE: rather than end with .TO so convert all these
        # to end with .TO
        updated_tickers = np.array([ticker[4:] + '.TO' if ticker[0:3] == 'TSE' else ticker for ticker in transaction_history['security']])
        transaction_history['security'] = updated_tickers

        # shift any date that is not a business day to the next business day
        transaction_history['date'] = transaction_history['date'] + 0 * BDay()

        self.df = transaction_history
    
    # ### WONT NEED THIS I THNK -----------------------------------------------------------------------
    # def transactions_on_date(self, date):
    #     '''
    #     Returns an itterable of the transactions from the
    #     transaction history on a given date
    #     '''
    #     transactions_on_date = self.transactions_df[self.transactions_df['date'] == date]
    #     return transactions_on_date.iterrows()