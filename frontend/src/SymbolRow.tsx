import React from "react";


export interface IStockData {
    stock: string;
    symbol: string;
    price: number;
    weight: number;
    shares: number;
    investment: number;
    composite_score: number;
    returns: {
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

interface ISymbolRow {
    rank: number;
    item: IStockData
};

// Round to 2 decimal places
const round_off = (num: number): number => {
    return Math.round(num * 100) / 100;
}

export const SymbolRow: React.FC<ISymbolRow> = ({ rank, item }): React.ReactElement => {
    return (
        <tr>
            <td>{rank}</td>
            <td className="stock-name">{item.stock}</td>
            <td>{item.symbol}</td>
            <td>{item.price}</td>
            <td>{item.weight}</td>
            <td>{item.shares}</td>
            <td>{round_off(item.investment)}</td>
            <td>{round_off(item.composite_score)}</td>
            <td className="returns">{round_off(item.returns['1y'].return)}</td>
            <td className="returns">{round_off(item.returns['1mo'].return)}</td>
            <td className="returns">{round_off(item.returns['1w'].return)}</td>
            <td>{round_off(item.returns['1y'].vwap)}</td>
            <td>{round_off(item.returns['1mo'].vwap)}</td>
            <td>{round_off(item.returns['1w'].vwap)}</td>
            <td>{round_off(item.returns['1y'].rsi)}</td>
            <td>{round_off(item.returns['1mo'].rsi)}</td>
            <td>{round_off(item.returns['1w'].rsi)}</td>
        </tr>
    );
};
