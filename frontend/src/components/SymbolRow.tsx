import React from "react";
import { ISymbolRow } from "./StockDataTypes";
import { TableCell, TableRow } from "@mui/material";


export const SymbolRow: React.FC<ISymbolRow> = ({ item, rank, headers }): React.ReactElement => {
    return (
        <TableRow key={rank}>

            {headers?.map((header, index) => {
                const value = item[header.key];
                const key = `${index}-${header.display}`;
                if (header.key === 'rank') {
                    return <TableCell key ={key} >
                        {rank}
                    </TableCell>
                }
                return header.cellTemplate?.(item[header.key], item) ?? <TableCell key={key}>{value}</TableCell>
            })}
        </TableRow>
    );
};