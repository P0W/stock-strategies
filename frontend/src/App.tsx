import { IHeader, StockTable } from './StockTable';
import { StockDatePicker } from './StockDatePicker';
import "./App.css";
import React from 'react';


// Round to 2 decimal places
const round_off = (num: number): number => {
  return Math.round(num * 100) / 100;
}

const ReturnsTemplate = (key: string, item: number) => {
  return <td className="returns" key={key}>{round_off(item)}</td>;
};

export const App = () => {
  const [toDateString, setToDateString] = React.useState<string>('');
  const [fromDateString, setFromDateString] = React.useState<string>('');

  const headers: IHeader[] = [
    {
      display: 'S.No.',
      key: 'rank'
    },
    {
      display: 'Stock',
      key: 'stock'
    },
    {
      display: 'Symbol',
      key: 'symbol'
    },
    {
      display: 'Price',
      key: 'price'
    },
    {
      display: 'Weight',
      key: 'weight'
    },
    {
      display: 'Shares',
      key: 'shares'
    },
    {
      display: 'Investment',
      key: 'investment'
    },
    {
      display: 'Score',
      key: 'composite_score'
    },
    {
      display: '1y',
      key: 'returns.1y.return',
      cellTemplate: ReturnsTemplate
    },
    {
      display: '1mo',
      key: 'returns.1mo.return',
      cellTemplate: ReturnsTemplate
    },
    {
      display: '1y',
      key: 'returns.1mo.return',
      cellTemplate: ReturnsTemplate
    },

  ];

  return (
    <div className="App">
      <div className="date-picker-container">
        <label>From:</label>
        <StockDatePicker onDateChange={setFromDateString} />
        <label>To:</label>
        <StockDatePicker onDateChange={setToDateString} />
      </div>
      <StockTable headers={headers} toDateString={toDateString} fromDateString={fromDateString} />
    </div>
  );
};

