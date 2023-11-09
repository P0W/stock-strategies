import React from "react";
import { IStockData, SymbolRow } from "./SymbolRow";
import './StockTable.css';


// const ENDPOINT = ' http://172.174.157.91:8080/json'; // 'http://localhost:8000/json';
export const StockTable: React.FC<{ date_string: string }> = ({ date_string }): React.ReactElement => {
    const [stocks, setStocks] = React.useState<IStockData[]>([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        fetch(`/json/${date_string}`)
            .then(res => res.json())
            .then(data => {
                setStocks(data[0]);
                setLoading(false);
            })
            .catch(err => {
                console.log(err);
                setLoading(false);
            });
    }, [date_string]);

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <table className="stock-table">
            <tr>
                <th>S.No.</th>
                <th>Stock</th>
                <th>Symbol</th>
                <th>Price</th>
                <th>Weight</th>
                <th>Shares</th>
                <th>Investment</th>
                <th>Score</th>
                <th>1yr</th>
                <th>1mo</th>
                <th>1w</th>
                <th>1yr_vwap</th>
                <th>1mo_vwap</th>
                <th>1w_vwap</th>
                <th>1y_rsi</th>
                <th>1mo_rsi</th>
                <th>1w_rsi</th>
            </tr>
            <tbody>
                {stocks.map((stock, index) => (
                    <SymbolRow key={index} item={stock} rank={index + 1} />
                ))}
            </tbody>
        </table>
    );
};