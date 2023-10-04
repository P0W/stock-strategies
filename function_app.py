## Azure Function app to run the momentum strategy
## Author: Prashant Srivastava

import os
import logging

import azure.functions as func

import get_stocks as strategy
from BlobService import BlobService

app = func.FunctionApp()


## Run the momentum strategy time triggered
@app.schedule(
    schedule="0 17 * * 1-5", arg_name="myTimer", run_on_startup=True, use_monitor=False
)
def momentum_strategy(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info("The timer is past due!")

    # Get the connection string
    connection_string = os.environ["AzureWebJobsStorage"]

    # Get the number of stocks and investment amount
    NUM_STOCKS = int(os.environ["NUM_STOCKS"])
    INVESTMENT_AMOUNT = float(os.environ["INVESTMENT_AMOUNT"])
    logging.info("Connection string: %s", connection_string)
    logging.info("Number of stocks: %d", NUM_STOCKS)
    logging.info("Investment amount: %.2f", INVESTMENT_AMOUNT)

    # Initialize the BlobServiceClient
    blob_service = BlobService(connection_string)

    # Define the name of the blob
    blob_name = strategy.get_file_name("all_symbols/nifty200-symbols")

    nifty200_symbols = blob_service.get_blob_data_if_exists(blob_name)
    if nifty200_symbols is None:
        logging.info("%s blob does not exist", blob_name)
        ## Get the list of stocks
        nifty200_symbols = strategy.getStockList()
        ## Upload the list of stocks
        blob_service.upload_blob(nifty200_symbols, blob_name)

    ## Upload the portfolio
    blob_name = strategy.get_file_name("portfolio-on")
    portfolio = blob_service.get_blob_data_if_exists(blob_name)
    if portfolio is None:
        logging.info("%s blob does not exist", blob_name)
        ## Build the portfolio
        portfolio = strategy.build_portfolio(
            nifty200_symbols, N=NUM_STOCKS, investment=INVESTMENT_AMOUNT
        )
        blob_service.upload_blob(portfolio, blob_name)

    ## Generate Rebalance json
    previous_day_blob_name = strategy.get_file_name("portfolio-on", days=1)
    previous_day_portfolio = blob_service.get_blob_data_if_exists(
        previous_day_blob_name
    )
    if previous_day_portfolio:
        blob_name = strategy.get_file_name("rebalances/rebalance-on")
        rebalance = blob_service.get_blob_data_if_exists(blob_name)
        if rebalance is None:
            logging.info("%s blob does not exist", blob_name)
            rebalance = strategy.rebalance_portfolio(previous_day_portfolio, portfolio)
            ## Upload the rebalance json
            blob_service.upload_blob(rebalance, blob_name)

    logging.info("Executed momentum strategy successfully!")
