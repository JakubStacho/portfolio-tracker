# Portfolio Tracker
Python code for tracking investment portfolio returns based on a given transaction history. Currently supports tracking of whole portfolio value and time weighted return to compare portfolio performance to a benchmark.

Portfolio activity must be documented in a transaction history file. This file needs to be in a specific format provided as a .csv file. An exmaple transaction history file with the correct format is provided in `transaction-files/sample-history.csv`. This transaction history file can be created and stored in Excel or Google Sheets and then periodically exported as a .csv for further analysis with this project.

#### Notes
Required python libraries are listed in `requirements.txt`.

## Examples

#### Portfolio Value
![Portfolio Value](./output/portfolio-value.png)

#### Time Weighted Portfolio Returns
![Portfolio Returns](./output/percent-returns.png)
