import React from "react";
import { IStockTable } from "./StockDataTypes";
import './StockTable.css';
import { SymbolRow } from "./SymbolRow";



export const StockTable: React.FC<IStockTable> = ({ headers, stockData }): React.ReactElement => {
    
    return (
        <table className="stock-table">
            <thead>
                <tr>
                    {headers?.map((header, index) => (
                        <th key={`${index}-${header.display}`}>{header.display}</th>
                    ))}
                </tr>
            </thead>

            <tbody>
                {stockData?.map((stock, index) => (
                    <SymbolRow key={`${index}-${stock.symbol}`} item={stock} rank={index + 1} headers={headers} />
                ))}
            </tbody>
        </table>
    );
};