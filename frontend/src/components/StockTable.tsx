import React from "react";
import { IStockTable } from "./StockDataTypes";
import { SymbolRow } from "./SymbolRow";
import { Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from "@mui/material";


export const StockTable: React.FC<IStockTable> = ({ headers, stockData }): React.ReactElement => {

    return (
        <TableContainer component={Paper}>
            <Table stickyHeader size="small" aria-label="sticky table">
                <TableHead >
                    <TableRow>
                        {headers?.map((header, index) => (
                            <TableCell key={`${index}-${header.display}`} style={{ textAlign: "center" }}>
                                <Typography sx={{
                                    fontWeight: 'bold',
                                    color: '#3f51b5'
                                }}>
                                    {header.display}
                                </Typography>
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>

                <TableBody>
                    {stockData?.map((stock, index) => (
                        <SymbolRow key={index} item={stock} rank={index + 1} headers={headers} />
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};