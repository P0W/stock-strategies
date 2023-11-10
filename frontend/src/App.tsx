import "./App.css";
import React from 'react';

import { StockTable } from './StockTable';
import { StockDatePicker } from './StockDatePicker';

import { IRebalanceData, IStockData } from './SymbolRow';
import { mainTableHeader, rebalanceTableHeader } from './StockTableHeader';
import { round_off } from './Utils';


const useData = (toDateString: string, fromDateString: string) => {
  const [toDateStocks, setToDateStocks] = React.useState<IStockData[]>([]);
  const [fromDateStocks, setFromDateStocks] = React.useState<IStockData[]>([]);
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
    //const nifty200Fetch = fetchData('nifty200', toDateString);
    const rebalanceFetch = fetchData('rebalance', fromDateString, toDateString);

    Promise.all([toFetch, fromFetch, rebalanceFetch])
      .then(data => {
        setToDateStocks(data[0][0]);
        setFromDateStocks(data[1][0]);
        setRebalanceData(data[2]["stocks"]);
        setCapitalIncurred(data[2]["capital_incurred"]);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, [fromDateString, toDateString]);

  return { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, loading };
};

export const App = () => {
  const [fromDateString, setFromDateString] = React.useState<string>('');
  const [toDateString, setToDateString] = React.useState<string>('');

  const { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, loading } = useData(toDateString, fromDateString);
  // Sum up the investment amount
  const fromInvestment = fromDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const toInvestment = toDateStocks.reduce((acc, stock) => acc + stock.investment, 0);

  return (
    <div className="App">
      <div className="date-picker-container">
        <label>From:</label>
        <StockDatePicker initialDate={fromDateString} onDateChange={setFromDateString} />
        <label>To:</label>
        <StockDatePicker initialDate={toDateString} onDateChange={setToDateString} />
      </div>
      {!loading ?
        <div>
          <div style={{ display: 'flex', padding: '50px', justifyContent: 'space-between' }}>
            <div className='stock-table-container'>
              <h4>Holding On: {fromDateString}</h4>
              <StockTable headers={mainTableHeader} stockData={fromDateStocks} />
              <p className='portfolio-value'>Total Investment: {round_off(fromInvestment)} INR | as on {fromDateString}</p>
            </div>
            <div className='stock-table-container'>
              <h4>Holding as on: {toDateString}</h4>
              <StockTable headers={mainTableHeader} stockData={toDateStocks} />
              <p className='portfolio-value'>Total Investment: {round_off(toInvestment)} INR | as on {toDateString}</p>
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

