import React from "react";
import { ISymbolRow } from "./StockDataTypes";

export const SymbolRow: React.FC<ISymbolRow> = ({ rank, item, headers }): React.ReactElement => {

    return (
        <tr key={rank}>
            {headers?.map((header, index) => {
                if (header.key === 'rank') {
                    return <td key={index}>{rank}</td>
                }
                return header.cellTemplate?.(item[header.key]) ?? <td key={`${index}-${header.key}`}>{item[header.key]}</td>
            })}
        </tr>
    );
};
