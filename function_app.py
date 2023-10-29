## Azure Function app to run the momentum strategy
## Author: Prashant Srivastava

import os
import logging

import azure.functions as func
import business

app = func.FunctionApp()


## Run the momentum strategy time triggered
@app.schedule(
    schedule="25 14,2 * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
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

    business.build_todays_portfolio(connection_string, NUM_STOCKS, INVESTMENT_AMOUNT)
    logging.info("Executed momentum strategy successfully!")


@app.route(route="portfolio", auth_level=func.AuthLevel.FUNCTION)
def portfolio(req: func.HttpRequest) -> func.HttpResponse:
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

    conn_string = os.environ["AzureWebJobsStorage"]

    table_html = business.view_portfolio(conn_string, request_date)
    if table_html:
        return func.HttpResponse(
            table_html, status_code=200, charset="utf-8", mimetype="text/html"
        )
    return func.HttpResponse("Portfolio not found", status_code=404, charset="utf-8")
