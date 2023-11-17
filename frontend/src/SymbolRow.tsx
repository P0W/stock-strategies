import React from "react";
import { ISymbolRow } from "./StockDataTypes";
import { TableRow, TableCell } from '@material-ui/core';


// export const SymbolRow: React.FC<ISymbolRow> = ({ rank, item, headers }): React.ReactElement => {

//     return (
//         <tr key={rank}>
//             {headers?.map((header, index) => {
//                 if (header.key === 'rank') {
//                     return <td key={index}>{rank}</td>
//                 }
//                 return header.cellTemplate?.(item[header.key], item) ?? <td key={`${index}-${header.key}`}>{item[header.key]}</td>
//             })}
//         </tr>
//     );
// };


export const SymbolRow: React.FC<ISymbolRow> = ({ item, rank, headers }): React.ReactElement => {
    return (
        <TableRow key={rank}>

            {headers?.map((header, index) => {
                const value = item[header.key];
                const key = `${index}-${header.display}`;
                // if (header.key === 'price' || header.key === 'investment') {
                //     value = parseFloat(value).toFixed(2);
                // }
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