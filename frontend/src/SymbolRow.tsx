import React from "react";
import { IHeader } from "./StockTable";


export interface IStockData {
    [key: string]: any;
    stock: string;
    symbol: string;
    price: number;
    weight: number;
    shares: number;
    investment: number;
    composite_score: number;

    returns: {
        [key: string]: any;
        '1y': {
            return: number;
            vwap: number;
            rsi: number;
        },
        '1mo': {
            return: number;
            vwap: number;
            rsi: number;
        },
        '1w': {
            return: number;
            vwap: number;
            rsi: number;
        }
    }
};

export interface IRebalanceData {
    [key: string]: any;
    symbol: string;
    amount: number;
    shares: number;
};

export interface INifty200Data {
    [key: string]: any;
    symbol: string;
    price: number;
    avg_price: number;
    diff: number;
};

interface ISymbolRow {
    rank: number;
    item: IStockData | IRebalanceData | INifty200Data;
    headers: IHeader[];
};

export const SymbolRow: React.FC<ISymbolRow> = ({ rank, item, headers }): React.ReactElement => {

    return (
        <tr key = {rank}>
            {headers?.map((header, index) => {
                if (header.key === 'rank') {
                    return <td key={index}>{rank}</td>
                }
                return header.cellTemplate?.(item[header.key]) ?? <td key={index}>{item[header.key]}</td>
            })}
        </tr>
    );
};
