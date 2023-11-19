// SidePanel.tsx
import React from 'react';
import { drawerWidth } from './Utils';
import { Box, Button, Divider, Drawer, Grid, InputAdornment, makeStyles, Stack, TextField, Typography } from '@mui/material';



interface ISidePanelProps {
    drawerOpen: boolean;
    numStocks: number;
    setNumStocks: (num: number) => void;
    investmentValue: number;
    setInvestmentValue: (value: number) => void;
    handleSignOut: () => void;
}

export const SidePanel: React.FC<ISidePanelProps> = ({ drawerOpen, numStocks, setNumStocks, investmentValue, setInvestmentValue, handleSignOut }) => {

    return (
        <Drawer variant="persistent" anchor="right" open={drawerOpen} >
            <Stack spacing={2} sx={{
                margin: '10px',
                marginTop: '42px',
            }} >

                <Button variant="text" onClick={handleSignOut} size="small" >
                    Sign Out
                </Button>
                <Divider />
                <Typography gutterBottom  >
                    Portfolio Configuration
                </Typography>
                <TextField type="number"
                    value={numStocks}
                    onChange={(e) => setNumStocks(Number(e.target.value))}
                    label="Number of Stocks"
                    size="small"
                    variant='standard'
                    sx={{
                        width: '100%',
                        marginRight: '1em',
                        paddingRight: '1em',
                    }}
                />
                <TextField type="number"
                    value={investmentValue}
                    onChange={(e) => setInvestmentValue(Number(e.target.value))}
                    InputProps={{
                        startAdornment: <InputAdornment position="start">INR</InputAdornment>,
                    }}
                    label="Investment Value"
                    size="small"
                    variant='standard'
                    sx={{
                        width: '100%',
                        marginRight: '1em',
                        paddingRight: '1em',
                    }}
                />

            </Stack>
        </Drawer>
    );
};