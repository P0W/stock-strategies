import React, { useState } from 'react';
import { Button, TextField, Grid, Paper, Typography, Link, Box } from '@material-ui/core';
import { useNavigate } from 'react-router-dom';

export const RegisterPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = (event: any) => {
        event.preventDefault();
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, confirmPassword })
        })
            .then((res) => {
                if (res.ok) {
                    return res.json();
                } else {
                    throw new Error('Invalid username or password');
                }
            })
            .then((data) => {
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
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                label="Confirm Password"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
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
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};
