import React from "react";
import { IRebalanceData, IStockData, SymbolRow } from "./SymbolRow";
import './StockTable.css';

export interface IHeader {
    display: string;
    key: string;
    cellTemplate?: (item: number) => React.ReactElement | null;
}

interface IStockTable {
    headers: IHeader[];
    stockData: IStockData[] | IRebalanceData[];
}


export const StockTable: React.FC<IStockTable> = ({ headers, stockData }): React.ReactElement => {
    
    return (
        <table className="stock-table">
            <thead>
                <tr>
                    {headers?.map((header, index) => (
                        <th key={index}>{header.display}</th>
                    ))}
                </tr>
            </thead>

            <tbody>
                {stockData?.map((stock, index) => (
                    <SymbolRow key={index} item={stock} rank={index + 1} headers={headers} />
                ))}
            </tbody>
        </table>
    );
};