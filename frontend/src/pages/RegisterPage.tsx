import React, { useState } from 'react';
import { Box, Button, Grid, Link, Paper, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { SHA256 } from 'crypto-js';
import { Copyright } from '../components/Utils';

export const RegisterPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = (event: any) => {
        event.preventDefault();
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        const hashedPassword = SHA256(password).toString();
        fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, hashedPassword, email, phoneNumber, fullName })
        })
            .then((res) => {
                if (res.ok) {
                    return res.json();
                } else {
                    throw new Error('Invalid username or password');
                }
            })
            .then(() => {
                navigate('/');
            })
            .catch((err) => {
                console.error(err);
                alert(err.message);
            });
    };

    const handleLogin = () => {
        navigate('/login');
    };

    return (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
            <Grid container justifyContent="center">
                <Grid item xs={12} sm={8} md={6} lg={4}>
                    <Paper style={{ padding: 16 }}>
                        <Typography variant="h4" align="center">
                            Register
                        </Typography>
                        <form onSubmit={handleRegister}>
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Full Name"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                required
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Phone Number"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Confirm Password"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                            {error && <p>{error}</p>}
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                color="primary"
                                style={{ marginTop: 16 }}
                            >
                                Register
                            </Button>
                        </form>
                        <Typography variant="body1" style={{ marginTop: 16, textAlign: 'center' }}>
                            Already have an account?{' '}
                            <Link component="button" variant="body2" onClick={handleLogin}>
                                Login
                            </Link>
                        </Typography>
                        <Copyright sx={{ mt: 5 }} />
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};
