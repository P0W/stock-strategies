# stock-strategies

Description
-------------
This repository contains a automated momentum based system that helps users fetch stock data from a web source (tickertape.in), 
calculate financial metrics, build and rebalance investment portfolios, and display portfolio information. 

It is designed to run as an Azure Function, making it easy to automate daily/weekly/monthly portfolio updates.

Key Features
-------------
* Fetches stock data from a web source (tickertape.in).
* Calculates financial metrics like RSI and VWAP for stock analysis for 1y, 1mo, 1w along with respective returns.
* Builds and rebalances portfolios based on momentum score.
* Stores portfolio results in an Azure Storage Account.
* Supports automated daily portfolio updates using Azure Functions.
