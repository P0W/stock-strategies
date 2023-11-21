import { Link, Typography } from "@mui/material";

// Round to 2 decimal places
export const round_off = (num: number): number => {
    return Math.round(num * 100) / 100;
}


export const drawerWidth = 200;

export const Copyright = (props: any) => {
    return (
        <Typography variant="body2" color="text.secondary" align="center" {...props}>
            {'Copyright © '}
            <Link color="inherit" >
                Prashant Srivastava
            </Link>{' '}
            {new Date().getFullYear()}
            {'.'}
        </Typography>
    );
}
