import { StockTable } from './StockTable';
import { useStockDate } from './useStockDate';
import "./App.css";

export const App = () => {
  const {DatePickerComponent, dateString} = useStockDate();
  return (
    <div className="App">
      <div className="date-picker-container">
        <label>From:</label>
        <DatePickerComponent />
        <label>To:</label>
        <DatePickerComponent />
      </div>
      <StockTable date_string={dateString}/>
    </div>
  );
};

