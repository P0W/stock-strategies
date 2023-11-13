import "./App.css";
import React from 'react';

import { StockTable } from './StockTable';
import { StockDatePicker } from './StockDatePicker';


import { mainTableHeader, nifty200TableHeader, rebalanceTableHeader } from './StockTableHeader';
import { round_off } from './Utils';
import { INifty200Data, IRebalanceData, IStockData, IToFromData } from "./StockDataTypes";

const useData = (toDateString: string, fromDateString: string) => {
  const [toDateStocks, setToDateStocks] = React.useState<IStockData[]>([]);
  const [fromDateStocks, setFromDateStocks] = React.useState<IStockData[]>([]);
  const [currentPrices, setCurrentPrices] = React.useState<INifty200Data[]>([]);
  const [rebalanceData, setRebalanceData] = React.useState<IRebalanceData[]>([]);
  const [capitalIncurred, setCapitalIncurred] = React.useState<number>(0);
  const [loading, setLoading] = React.useState(true);
  const cache = React.useRef<{ [key: string]: IStockData[] }>({});

  const fetchData = async (endpoint: string, fromDate: string, toDate?: string) => {
    const urlEndPoint = toDate ? `/${endpoint}/${fromDate}/${toDate}` : `/${endpoint}/${fromDate}`;
    if (cache.current[urlEndPoint]) {
      return Promise.resolve(cache.current[urlEndPoint]);
    } else {
      const res = await fetch(urlEndPoint);
      const data = await res.json();
      cache.current[urlEndPoint] = data;
      return data;
    }
  };


  React.useEffect(() => {
    if (!fromDateString || !toDateString) return;
    setLoading(true);
    const toFetch = fetchData('portfolio', toDateString);
    const fromFetch = fetchData('portfolio', fromDateString);
    const nifty200Fetch = fetchData('nifty200', toDateString);
    const rebalanceFetch = fetchData('rebalance', fromDateString, toDateString);

    Promise.all([toFetch, fromFetch, rebalanceFetch, nifty200Fetch])
      .then(data => {
        const pastStocksData = data[1][0] as IStockData[];
        const presentStocksData = data[0][0] as IStockData[];
        const rebalanceStocksData = data[2] as unknown as { [key: string]: any };
        const nifty200 = data[3] as { [key: string]: number };

        // get the prices for the stocks in the fromDateStocks from nifty200
        const currentStockPrice = pastStocksData.map(stock => {
          const thisStock = Object.keys(nifty200)?.find(niftyStock => niftyStock === stock.symbol);
          if (thisStock) {
            return {
              symbol: stock.symbol,
              price: nifty200[thisStock],
              avg_price: stock.price,
              diff: (nifty200[thisStock] - stock.price) / stock.price * 100,
              shares: stock.shares
            } as INifty200Data;
          }
          return { symbol: stock.symbol, price: -1, avg_price: stock.price, diff: -1 } as INifty200Data;
        });

        // Set states
        setFromDateStocks(pastStocksData);
        setToDateStocks(presentStocksData);
        setRebalanceData(rebalanceStocksData["stocks"] as IRebalanceData[]);
        setCapitalIncurred(rebalanceStocksData["capital_incurred"]);
        setCurrentPrices(currentStockPrice);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, [fromDateString, toDateString]);

  return { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, currentPrices, loading };
};

export const App = () => {
  const [fromDateString, setFromDateString] = React.useState<string>('');
  const [toDateString, setToDateString] = React.useState<string>('');

  const { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, currentPrices, loading } = useData(toDateString, fromDateString);
  // Sum up the investment amount
  const fromInvestment = fromDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const toInvestment = toDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const currentPortfolioValue = (currentPrices as IToFromData[]).reduce((acc, stock) => acc + stock.shares * stock.price, 0);

  return (
    <div className="App">
      <h3> Nifty-200 Momentum Strategy Analyzer</h3>
      <div className="date-picker-container">
        <label>From:</label>
        <StockDatePicker initialDate={fromDateString} onDateChange={setFromDateString} />
        <label>To:</label>
        <StockDatePicker initialDate={toDateString} onDateChange={setToDateString} />
      </div>
      {!loading ?
        <div>
          <div style={{ display: 'flex' }}>
            <div className='stock-table-container'>
              <label className="table-title">Investment: {round_off(fromInvestment)} INR | as on {fromDateString}</label>
              <StockTable headers={mainTableHeader} stockData={fromDateStocks} />
            </div>
            <div className='stock-table-container'>
              <label className="table-title">Current: {round_off(currentPortfolioValue)} INR | as on {toDateString}</label>
              <StockTable headers={nifty200TableHeader} stockData={currentPrices} />
            </div>
            <div className='stock-table-container'>
              <label className="table-title">New Investment: {round_off(toInvestment)} INR | as on {toDateString}</label>
              <StockTable headers={mainTableHeader} stockData={toDateStocks} />
            </div>

          </div>
          <div className='stock-table-container'>
            <h4> Rebalances</h4>
            <p className='portfolio-value'> Capital Incurred: {round_off(capitalIncurred)} INR | from {fromDateString} to {toDateString}</p>
            <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />

          </div>
        </div> : fromDateString != '' && toDateString != '' && <div> Loading... </div>
      }
    </div>
  );
};

