[![Build](https://github.com/P0W/stock-strategies/actions/workflows/node.js.yml/badge.svg?branch=main)](https://github.com/P0W/stock-strategies/actions/workflows/node.js.yml)

# stock-strategies 

Description
-------------
This repository contains a automated momentum based system that helps users fetch stock data from a web source (tickertape.in), 
calculate financial metrics, build and rebalance investment portfolios, and display portfolio information. 

It is designed to run as an Azure Function, making it easy to automate daily/weekly/monthly portfolio updates.

[**`Live Hosted on Azure`**](https://172.174.157.91/show)

![**Sample**](https://github.com/P0W/stock-strategies/blob/main/stock-strategies.png)

Backtesting
------------
* Used only returns values over last 1y, 1mo, 1w, 1d
* Negative total_incurred amount represent inflow of money to trading account (profit)
* Detailed csv report permuted over various parameters can be seen here [``Backtest Report``](https://github.com/P0W/stock-strategies/blob/main/backtest/output.csv)
  - time frames for rebalances
  - investement amount
  - number of stocks
* The report is sorted with max draw down parameter (lowest first)
* Rebalances for given period,number of stocked picked, investment amount can be seen here [``Rebalances Reports``](https://github.com/P0W/stock-strategies/blob/main/backtest/temp)

Key Features
-------------
* Fetches stock data from a web source (tickertape.in).
* Calculates financial metrics like RSI and VWAP for stock analysis for 1y, 1mo, 1w along with respective returns.
* Builds and rebalances portfolios based on momentum score.
* Stores portfolio results in an Azure Storage Account.
* Supports automated daily portfolio updates using Azure Functions.


Composite Score Calculation
----------------------------
The heart of the Momentum Picking Strategy lies in the calculation of a composite score for each stock. This score is derived from three crucial financial metrics, each assigned a predefined weight:

* Returns: This metric assesses a stock's historical returns over different time frames, typically one year, one month, and one week. The returns are normalized to ensure comparability.
* VWAP (Volume-Weighted Average Price): VWAP reflects the average price of a stock over a specific period, giving more weight to prices with higher trading volumes. Normalized VWAP values are considered.
* RSI (Relative Strength Index): RSI is a momentum oscillator measuring the speed and change of price movements. Normalized RSI values are used.

Weighting
---------
Each of the three metrics (Returns, VWAP, and RSI) is assigned a weight that represents its importance in the composite score. These weights are customizable, allowing investors to adjust the strategy based on their preferences.

Normalization
--------------
To ensure that all metrics are on a consistent scale, they are normalized. This process scales the values so that they have similar ranges, making them directly comparable.

Composite Score Calculation
----------------------------
The composite score for a stock is calculated as a weighted sum of the normalized values of the three metrics. The formula is as follows:
```
Composite Score = (Weight_Returns * Sum(Normalized_Returns))
               + (Weight_VWAP * Sum(Normalized_VWAP))
               + (Weight_RSI * Sum(Normalized_RSI))
```

Interpretation
--------------
Stocks with higher composite scores are considered to have stronger momentum. Investors can use this score to identify potential candidates for their portfolios, focusing on stocks with higher scores as they have exhibited stronger recent performance based on the selected metrics.

