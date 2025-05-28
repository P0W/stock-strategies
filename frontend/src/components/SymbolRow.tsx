import React from "react";
import { ISymbolRow } from "./StockDataTypes";
import { TableCell, TableRow } from "@mui/material";


export const SymbolRow: React.FC<ISymbolRow> = ({ item, rank, headers }): React.ReactElement => {
    return (
        <TableRow key={rank}>

            {headers?.map((header, index) => {
                const value = item[header.key];
                const key = `${rank}-${index}-${header.display}`;
                if (header.key === 'rank') {
                    return <TableCell key={key} >
                        {rank}
                    </TableCell>
                }
                
                if (header.cellTemplate) {
                    const templateResult = header.cellTemplate(item[header.key], item);
                    if (templateResult) {
                        return React.cloneElement(templateResult, { key });
                    }
                }
                
                return <TableCell key={key}>{value}</TableCell>
            })}
        </TableRow>
    );
};