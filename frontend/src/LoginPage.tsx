import React, { useState } from 'react';
import { Button, TextField, Grid, Paper, Typography, Link, Box } from '@material-ui/core';
import { useNavigate } from 'react-router-dom';


export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = (event: any) => {
    event.preventDefault();
    // Handle login logic here
    navigate('/app');
  };

  const handleSignUp = () => {
    navigate('/register');
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
      <Grid container justifyContent="center">
        <Grid item xs={12} sm={8} md={6} lg={4}>
          <Paper style={{ padding: 16 }}>
            <Typography variant="h4" align="center">
              Login
            </Typography>
            <form onSubmit={handleLogin}>
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
              <Button
                type="submit"
                fullWidth
                variant="contained"
                color="primary"
                style={{ marginTop: 16 }}
              >
                Login
              </Button>
            </form>
            <Typography variant="body1" style={{ marginTop: 16, textAlign: 'center' }}>
              Don't have an account?{' '}
              <Link component="button" variant="body2" onClick={handleSignUp}>
                Sign up
              </Link>
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};