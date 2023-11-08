import datetime
import json
import logging

import get_stocks as strategy
from BlobService import BlobService

logging = logging.getLogger(__name__)

def round_off(value: float) -> float:
    return round(value, 2)


def build_todays_portfolio(
    connection_string: str, NUM_STOCKS: int, INVESTMENT_AMOUNT: int
):
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

    return portfolio


def get_portfolio(conn_string: str, request_date: str = None) -> str:
    blob_service = BlobService(conn_string)
    if request_date:
        portfolio_blob_name = f"portfolio-on-{request_date}.json"
    else:
        portfolio_blob_name = strategy.get_file_name("portfolio-on")
    logging.info("Portfolio blob name: %s", portfolio_blob_name)
    return blob_service.get_blob_data_if_exists(portfolio_blob_name), portfolio_blob_name

def view_portfolio(conn_string: str, request_date: str = None, detailed_view:bool = True) -> str:
    portfolio, portfolio_blob_name = get_portfolio(conn_string, request_date)
    blob_service = BlobService(conn_string)
    if portfolio:
        # Generate an HTML table
        table_html = """
            <title>Momentum Strategy</title>
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
            
            .returns { font-size: 18px; }
            
            .date-button { background: #0074cc; color: white; border: none; padding: 5px 10px; margin-bottom: 5px; }
            
            .percentage-change-container { margin-left: 20px; }
            
            .change-item { font-family: Arial, sans-serif; }
        </style>"""
        table_html += """
        <script>
            
            function toggleData(button) {
                var dataContainer = button.nextElementSibling;
                if (dataContainer.style.display === 'none') {
                    dataContainer.style.display = 'block';
                } else {
                    dataContainer.style.display = 'none';
                }
            }
            
            function plotLineChartWithCircles(data, canvasId) {
                const canvas = document.getElementById(canvasId);
                const ctx = canvas.getContext("2d");

                canvas.width = 800;
                canvas.height = 400;

                const margin = 40;
                const chartWidth = canvas.width - 2 * margin;
                const chartHeight = canvas.height - 2 * margin;

                const minDate = new Date(data[0].date);
                const maxDate = new Date(data[data.length - 1].date);
                const minValue = Math.min(...data.map((item) => item.per_change));
                const maxValue = Math.max(...data.map((item) => item.per_change));

                function dateToX(date) {
                    return (
                    ((date - minDate) / (maxDate - minDate)) * chartWidth + margin
                    );
                }

                function valueToY(value) {
                    return canvas.height - (((value - minValue) / (maxValue - minValue)) * chartHeight + margin);
                }

                // Draw X and Y axes
                ctx.strokeStyle = "black";
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(margin, margin);
                ctx.lineTo(margin, canvas.height - margin);
                ctx.lineTo(canvas.width - margin, canvas.height - margin);
                ctx.stroke();

                // Draw X-axis label
                ctx.fillStyle = "black";
                ctx.font = "16px Arial";
                ctx.textAlign = "center";
                ctx.fillText("Date", canvas.width / 2, canvas.height - 10);

                // Draw Y-axis label
                ctx.save();
                ctx.translate(10, canvas.height / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Returns", 0, 0);
                ctx.restore();

                // Draw X-axis tick marks and labels
                ctx.fillStyle = "black";
                ctx.font = "12px Arial";
                ctx.textAlign = "center";
                const xStep = chartWidth / 10;
                for (let i = 1; i <= 10; i++) {
                    const x = margin + i * xStep;
                    ctx.beginPath();
                    ctx.moveTo(x, canvas.height - margin - 5);
                    ctx.lineTo(x, canvas.height - margin + 5);
                    ctx.stroke();
                    const date = new Date(minDate.getTime() + (i / 10) * (maxDate - minDate));
                    ctx.fillText(date.toISOString().slice(0, 10), x, canvas.height - margin + 20);
                }

                // Draw Y-axis tick marks and labels
                ctx.textAlign = "right";
                const yStep = chartHeight / 10;
                for (let i = 1; i <= 10; i++) {
                    const y = canvas.height - margin - i * yStep;
                    ctx.beginPath();
                    ctx.moveTo(margin - 5, y);
                    ctx.lineTo(margin + 5, y);
                    ctx.stroke();
                    const value = minValue + (i / 10) * (maxValue - minValue);
                    ctx.fillText(value.toFixed(2), margin - 10, y);
                }


                ctx.strokeStyle = "blue";
                ctx.lineWidth = 2;

                for (let i = 1; i < data.length; i++) {
                    const x1 = dateToX(new Date(data[i - 1].date));
                    const y1 = valueToY(data[i - 1].per_change);
                    const x2 = dateToX(new Date(data[i].date));
                    const y2 = valueToY(data[i].per_change);

                    // Draw a line connecting the data points
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();

                    // Circle the data points
                    ctx.beginPath();
                    ctx.arc(x1, y1, 4, 0, Math.PI * 2);
                    ctx.fillStyle = "red";
                    ctx.fill();

                    // If you also want to circle the last data point
                    if (i === data.length - 1) {
                    ctx.beginPath();
                    ctx.arc(x2, y2, 4, 0, Math.PI * 2);
                    ctx.fill();
                    }
                }
            }
        </script>
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
        if not detailed_view:
            return table_html

        ## Fetch all capital_incurred from the rebalance history
        ## Todays till the last strategy.get_file_name("rebalances/rebalance-on") available
        end_date = current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        ## Loop while the rebalance history blob exists
        history = {}
        # get list of last 30 dates in the format YYYY-MM-DD
        logging.info("Showing rebalances history")
        current_portfolio = blob_service.get_blob_data_if_exists(
            strategy.get_file_name("portfolio-on")
        )
        blob_name = strategy.get_file_name("all_symbols/nifty200-symbols")
        nifty200_symbols = blob_service.get_blob_data_if_exists(blob_name)
        while current_portfolio and nifty200_symbols:
            ## Keep going back in time in YYYY-MM-DD format
            current_date = datetime.datetime.strptime(
                current_date, "%Y-%m-%d"
            ) - datetime.timedelta(days=1)
            current_date = current_date.strftime("%Y-%m-%d")
            try:
                portfolio_blob_name = f"portfolio-on-{current_date}.json"
                logging.info("Fetching for %s", portfolio_blob_name)
                portfolio = blob_service.get_blob_data_if_exists(portfolio_blob_name)
                if portfolio:
                    logging.info("Portfolio found for %s", current_date)
                    rebalance = strategy.rebalance_portfolio(
                        portfolio,
                        current_portfolio,
                        strategy.build_price_list(nifty200_symbols),
                    )
                    logging.info("Rebalancing for %s", current_date)
                    history[current_date] = {
                        "capital_incurred": rebalance["capital_incurred"],
                        "start_date": current_date,
                        "end_date": end_date,
                        "num_days": (
                            datetime.datetime.strptime(end_date, "%Y-%m-%d")
                            - datetime.datetime.strptime(current_date, "%Y-%m-%d")
                        ).days,
                    }
                else:
                    logging.error("Portfolio not found for %s | Stopped", current_date)
                    break
            except Exception as e:
                logging.error(e)
                break

        ## valid current_date is one day before
        current_date = datetime.datetime.strptime(
            current_date, "%Y-%m-%d"
        ) + datetime.timedelta(days=1)
        current_date = current_date.strftime("%Y-%m-%d")
        ## For all porfolio from current_date till end_date calculate daily returns for each of them and store day wise
        daily_returns = {}
        while current_date != end_date:
            ## pick the portfolio for current_date
            this_date = current_date
            portfolio_blob_name = f"portfolio-on-{this_date}.json"
            logging.info("Fetching for %s", portfolio_blob_name)
            portfolio = blob_service.get_blob_data_if_exists(portfolio_blob_name)
            while portfolio and this_date != end_date:
                this_date = datetime.datetime.strptime(
                    this_date, "%Y-%m-%d"
                ) + datetime.timedelta(days=1)
                this_date = this_date.strftime("%Y-%m-%d")
                if portfolio:
                    ## for all days from current_date till end_date calculate daily returns
                    per_change, d1_p, d2_p = get_portfolio_value(
                        blob_service, portfolio, this_date
                    )
                    key = f"{current_date} | {round_off(d2_p)} INR"
                    if key not in daily_returns:
                        daily_returns[key] = []
                    daily_returns[key].append(
                        {
                            "per_change": per_change,
                            "date": this_date,
                            "current_value": d1_p,
                        }
                    )
            current_date = datetime.datetime.strptime(
                current_date, "%Y-%m-%d"
            ) + datetime.timedelta(days=1)
            current_date = current_date.strftime("%Y-%m-%d")

        logging.info("Daily Returns : %s", json.dumps(daily_returns, indent=2))

        ## Display the capital incurred history, style it
        table_html += "<p class='rebalance-updates'>Capital Incurred History</p>"
        table_html += """
        <table>
        <tr>
            <th>Purchased on</th>
            <th>End Date</th>
            <th>Num of Days</th>
            <th>Capital incurred</th>
        </tr>
        """
        for date, items in history.items():
            table_html += (
                f"<tr>"
                f"<td>{date}</td>"
                f"<td>{items['end_date']}</td>"
                f"<td>{items['num_days']}</td>"
                f"<td>{round_off(items['capital_incurred'])}</td>"
                f"</tr>"
            )
        table_html += "</table>"

        # Create an HTML structure in Python
        table_html += "<div class='returns'>Daily Returns</div>"
        drawScript = ""
        for date, items in daily_returns.items():
            table_html += (
                f"<div class='date-button' onclick=\"toggleData(this)\">{date}</div>"
            )
            table_html += (
                "<div class='percentage-change-container' style='display: none;'>"
            )
            table_html += (
                f"<table>"
                f"<tr>"
                f"<th>Date</th>"
                f"<th>Current Value</th>"
                f"<th>Return</th>"
            )
            for subitem in items:
                ## show as a table
                table_html += (
                    f"<tr>"
                    f"<td>{subitem['date']}</td>"
                    f"<td>{round_off(subitem['current_value'])}</td>"
                    f"<td>{round_off(subitem['per_change'])} %</td>"
                    f"</tr>"
                )
            table_html += "</table>"
            canvasId = f"chart-canvas-{date}"
            if len(items) >= 3:  ## Atleast 3 items to draw a line chart
                table_html += f"<canvas id='{canvasId}'></canvas>"
                drawScript += (
                    f"plotLineChartWithCircles({json.dumps(items)}, '{canvasId}');"
                )
            table_html += "</div>"
        table_html += "<script>" + drawScript + "</script>"

        return table_html
    return None


def get_portfolio_value(blob_service: BlobService, portfolio, this_date: str):
    logging.info("Getting portfolio change for %s", this_date)
    ## add 1 day to the present date
    this_date = datetime.datetime.strptime(this_date, "%Y-%m-%d")
    this_date = this_date.strftime("%Y-%m-%d")
    next_day_nifty200_symbols = blob_service.get_blob_data_if_exists(
        f"all_symbols/nifty200-symbols-{this_date}.json"
    )

    if next_day_nifty200_symbols and portfolio:
        price_list = strategy.build_price_list(next_day_nifty200_symbols)
        today_value = sum(
            [stock["shares"] * price_list[stock["symbol"]] for stock in portfolio]
        )
        previous_date_value = sum(
            [stock["shares"] * stock["price"] for stock in portfolio]
        )
        logging.info("Today value: %s", today_value)
        logging.info("Previous date value: %s", previous_date_value)
        ## return percentage change
        pc = round_off((today_value - previous_date_value) / previous_date_value * 100)
        return pc, today_value, previous_date_value
