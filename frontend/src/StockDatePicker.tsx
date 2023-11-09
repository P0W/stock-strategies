
import React, { useState } from "react";
import DatePicker from "react-datepicker";

import "react-datepicker/dist/react-datepicker.css";

export const StockDatePicker: React.FC<{ onDateChange: (date_string: string) => void }> = ({ onDateChange }) => {
    return (
        <DatePicker
            onChange={(date: Date | null) => {
                onDateChange(date ? date.toISOString().split('T')[0] : '');
            }}
            dateFormat='yyyy-MM-dd'
            placeholderText='Select a date'
        />
    );
};