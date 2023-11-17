// Round to 2 decimal places
export const round_off = (num: number): number => {
    return Math.round(num * 100) / 100;
}

export const round_off_str = (num: string): string => {
    return parseFloat(num).toFixed(2);
}

export const drawerWidth = 200;