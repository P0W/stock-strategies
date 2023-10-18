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
    schedule="0 3 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
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
            rebalance = strategy.rebalance_portfolio(
                previous_day_portfolio,
                portfolio,
                strategy.build_price_list(nifty200_symbols),
            )
            ## Upload the rebalance json
            blob_service.upload_blob(rebalance, blob_name)

    logging.info("Executed momentum strategy successfully!")


def round_off(value: float) -> float:
    return round(value, 2)


@app.route(route="portfolio", auth_level=func.AuthLevel.FUNCTION)
def portfolio(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    request_date = req.params.get("date")
    
    if not request_date:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            request_date = req_body.get("date")
    else:
        logging.info("Got date from param : %s", request_date)

    if request_date:
        portfolio_blob_name = f"portfolio-on-{request_date}.json"
    else:
        portfolio_blob_name = strategy.get_file_name("portfolio-on")

    logging.info("Portfolio blob name: %s", portfolio_blob_name)

    blob_service = BlobService(os.environ["AzureWebJobsStorage"])
    portfolio = blob_service.get_blob_data_if_exists(portfolio_blob_name)
    if portfolio:
        # Generate an HTML table
        table_html = """
            <style>
            table {
                border-collapse: collapse;
                width: 100%;
                font-size: 16px;
            }
            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            th {
                background-color: #4CAF50;
                color: white;
            }
             .portfolio-value {
                font-size: 18px;
                font-weight: bold;
                color: #007bff; /* Blue color */
                margin-top: 10px;
            }
            .rebalance-updates { font-size: 18px; font-weight: bold; color: #007bff; margin-top: 10px; }
        </style>"""
        table_html += """
        <table>
        <tr>
            <th>S.No.</th>
            <th>Stock</th>
            <th>Symbol</th>
            <th>Price</th>
            <th>1yr</th>
            <th>1mo</th>
            <th>1w</th>
            <th>1yr_vwap</th>
            <th>1mo_vwap</th>
            <th>1w_vwap</th>
            <th>1y_rsi</th>
            <th>1mo_rsi</th>
            <th>1w_rsi</th>
            <th>Score</th>
            <th>Weight</th>
            <th>Shares</th>
            <th>Investment</th>
        </tr>
        """
        rank = 1
        portfolio_value = 0
        for item in portfolio:
            table_html += (
                f"<tr>"
                f"<td>{rank}</td>"
                f"<td>{item['stock']}</td>"
                f"<td>{item['symbol']}</td>"
                f"<td>{round_off(item['price'])}</td>"
                f"<td>{round_off(item['returns']['1y']['return'])}</td>"
                f"<td>{round_off(item['returns']['1mo']['return'])}</td>"
                f"<td>{round_off(item['returns']['1w']['return'])}</td>"
                f"<td>{round_off(item['returns']['1y']['vwap'])}</td>"
                f"<td>{round_off(item['returns']['1mo']['vwap'])}</td>"
                f"<td>{round_off(item['returns']['1w']['vwap'])}</td>"
                f"<td>{round_off(item['returns']['1y']['rsi'])}</td>"
                f"<td>{round_off(item['returns']['1mo']['rsi'])}</td>"
                f"<td>{round_off(item['returns']['1w']['rsi'])}</td>"
                f"<td>{round_off(item['composite_score'])}</td>"
                f"<td>{round_off(item['weight'])}</td>"
                f"<td>{round_off(item['shares'])}</td>"
                f"<td>{round_off(item['investment'])}</td>"
                f"</tr>"
            )
            rank += 1
            portfolio_value += item["investment"]

        # Add the portfolio value paragraph with styling
        table_html += f"<tr><td colspan='17'><p class='portfolio-value'>Portfolio value: {round_off(portfolio_value)} INR | {portfolio_blob_name.split('.')[0]}</p></td></tr>"

        table_html += "</table>"

        ## Show a rebalance table updates, write a lable and style it
        table_html += "<h3>Rebalance updates</h3>"
        rebalance = None
        if not request_date:
            rebalance_blob_name = strategy.get_file_name("rebalances/rebalance-on")
            rebalance = blob_service.get_blob_data_if_exists(rebalance_blob_name)
        else:
            ## do a manual rebalance with todays portfolio
            logging.info("Manual rebalance with todays portfolio")
            current_portfolio = blob_service.get_blob_data_if_exists(
                strategy.get_file_name("portfolio-on")
            )
            if current_portfolio:
                blob_name = strategy.get_file_name("all_symbols/nifty200-symbols")
                nifty200_symbols = blob_service.get_blob_data_if_exists(blob_name)
                try:
                    rebalance = strategy.rebalance_portfolio(
                        portfolio,
                        current_portfolio,
                        strategy.build_price_list(nifty200_symbols),
                    )
                except Exception as e:
                    logging.error(e)
                    rebalance = None
            else:
                logging.error("Current portfolio not found")
        if rebalance:
            capital_incurred = rebalance["capital_incurred"]
            ## Display above as tabular format
            table_html += """
            <table>
            <tr>
                <th>Stock</th>
                <th>Shares</th>
                <th>Amount</th>
                <th>Action</th>
            </tr>
            """
            for item in rebalance["stocks"]:
                action = "HOLD"
                if item["shares"] > 0:
                    action = "BUY"
                elif item["shares"] < 0:
                    action = "SELL"
                table_html += (
                    f"<tr>"
                    f"<td>{item['symbol']}</td>"
                    f"<td>{item['shares']}</td>"
                    f"<td>{round_off(item['amount'])}</td>"
                    f"<td>{action}</td>"
                    f"</tr>"
                )
            table_html += "</table>"
            ## Display the capital incurred, style it
            table_html += f"<p class='rebalance-updates'>Capital incurred: {round_off(capital_incurred)} INR</p>"
        else:
            table_html += "<p class='rebalance-updates'>No rebalance updates</p>"

        return func.HttpResponse(
            table_html, status_code=200, charset="utf-8", mimetype="text/html"
        )
    else:
        return func.HttpResponse(
            "Portfolio not found", status_code=404, charset="utf-8"
        )
