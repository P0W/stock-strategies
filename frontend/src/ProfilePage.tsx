import * as React from 'react';
import { Button, TextField, Box, Grid, Paper, Typography, LinearProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { User } from './hooks/useUser';
import { useAuth } from './hooks/useAuth';


const ProfilePage = () => {
    const [formData, setFormData] = React.useState<User>();
    const [loading, setLoading] = React.useState(true);
    const { login } = useAuth();

    const navigate = useNavigate();

    React.useEffect(() => {
        // Fetch profile data here
        fetch('/profile', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        })
            .then((res) => {
                if (res.ok) {
                    return res.json();
                } else {
                    throw new Error('Invalid username or password');
                }
            })
            .then((data) => {
                setFormData({
                    fullName: data.fullName,
                    email: data.email,
                    phoneNumber: data.phoneNumber,
                    num_stocks: data.num_stocks,
                    investment: data.investment,
                });
                setLoading(false);
            })
            .catch((err) => {
                console.error(err);
                alert(err.message);
            });
    }, []);


    const handleCancel = () => {
        navigate(-1);
    };

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const target = event.target as HTMLInputElement;
        const id = target.id;
        switch (id) {
            case 'name':
                setFormData({ ...formData, fullName: target.value });
                break;
            case 'email':
                setFormData({ ...formData, email: target.value });
                break;
            case 'phone-number':
                setFormData({ ...formData, phoneNumber: target.value });
                break;
            case 'number-of-stocks':
                setFormData({ ...formData, num_stocks: parseInt(target.value) });
                break;
            case 'portfolio-value':
                setFormData({ ...formData, investment: parseInt(target.value) });
                break;
            default:
                console.log('Unknown input field');
                break;
        }
    };

    const handleSave = async () => {
        try {
            const response = await fetch('/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                throw new Error('Failed to save profile');
            }

            // Handle successful save here
            login(formData ?? {});
        } catch (error) {
            console.error(error);
        }
        navigate(-1);
    };

    return (
        !loading ? <Grid container justifyContent="center" alignItems="center" style={{ minHeight: '100vh' }}>
            <Grid item xs={12} sm={8} md={6}>
                <Paper elevation={3} sx={{ p: 4, mt: 3 }}>
                    <Typography variant="h5" align="center" mb={2}>Profile Information</Typography>
                    <Box
                        component="form"
                        sx={{
                            '& .MuiTextField-root': { m: 1, width: '100%' },
                        }}
                        noValidate
                        autoComplete="off"
                    >
                        <TextField required id="name" label="Full Name" defaultValue={formData?.fullName} onChange={handleChange} />
                        <TextField id="email" label="Email" defaultValue={formData?.email} onChange={handleChange} />
                        <TextField id="phone-number" label="Phone Number" defaultValue={formData?.phoneNumber} onChange={handleChange} />
                        <TextField required id="number-of-stocks" label="Number of Stocks" defaultValue={formData?.num_stocks} onChange={handleChange} />
                        <TextField required id="portfolio-value" label="Portfolio Value in INR" defaultValue={formData?.investment} onChange={handleChange} />
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                            <Button variant="outlined" sx={{ mr: 1 }} onClick={handleCancel}>Cancel</Button>
                            <Button variant="contained" onClick={handleSave}>Save</Button>
                        </Box>
                    </Box>
                </Paper>
            </Grid>
        </Grid> : <LinearProgress />

    );
}

export default ProfilePage;