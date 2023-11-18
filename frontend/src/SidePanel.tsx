// SidePanel.tsx
import React from 'react';
import { Box, Typography, Grid, TextField, Drawer, Button, makeStyles } from '@material-ui/core';
import { drawerWidth } from './Utils';

const useStyles = makeStyles((theme) => ({
    container: {
        margin: theme.spacing(10, 2, 0),
    },
    item: {
        margin: theme.spacing(1, 0),
    },
    drawer: {
        width: `calc(100% - ${drawerWidth}px)`,
        marginLeft: drawerWidth,
    },
    signOutButton: {
        fontWeight: 'bold',
    },
}));

interface ISidePanelProps {
    drawerOpen: boolean;
    numStocks: number;
    setNumStocks: (num: number) => void;
    investmentValue: number;
    setInvestmentValue: (value: number) => void;
    handleSignOut: () => void;
}

export const SidePanel: React.FC<ISidePanelProps> = ({ drawerOpen, numStocks, setNumStocks, investmentValue, setInvestmentValue, handleSignOut }) => {
    const classes = useStyles();

    return (
        <Drawer variant="persistent" anchor="left" open={drawerOpen} className={classes.drawer}>
            <Box my={2} className={classes.container}>
                <Button variant="text" onClick={handleSignOut} size="large" className={classes.signOutButton}>
                    Sign Out
                </Button>
                <Typography variant="h6" className={classes.item}>Configurations</Typography>
                <Grid container spacing={3} alignItems="center">
                    <Grid item className={classes.item}>
                        <Typography>Number of Stocks:</Typography>
                        <TextField type="number" value={numStocks} onChange={(e) => setNumStocks(Number(e.target.value))} />
                    </Grid>
                    <Grid item className={classes.item}>
                        <Typography>Investment Value:</Typography>
                        <TextField type="number" value={investmentValue} onChange={(e) => setInvestmentValue(Number(e.target.value))} />
                    </Grid>
                </Grid>
            </Box>
        </Drawer>
    );
};