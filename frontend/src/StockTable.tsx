import React from "react";
import { IStockTable } from "./StockDataTypes";
import { SymbolRow } from "./SymbolRow";
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, makeStyles, Typography } from '@material-ui/core';


const useStyles = makeStyles({
    tableHeader: {
        fontWeight: 'bold',
        color: '#3f51b5'
    },
});


export const StockTable: React.FC<IStockTable> = ({ headers, stockData }): React.ReactElement => {
    const classes = useStyles();

    return (
        <TableContainer component={Paper}>
            <Table stickyHeader size="small" aria-label="sticky table">
                <TableHead >
                    <TableRow>
                        {headers?.map((header, index) => (
                            <TableCell key={`${index}-${header.display}`}>
                                <Typography className={classes.tableHeader}>
                                    {header.display}
                                </Typography>
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>

                <TableBody>
                    {stockData?.map((stock, index) => (
                        <SymbolRow key={`${index}-${stock.symbol}`} item={stock} rank={index + 1} headers={headers} />
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};