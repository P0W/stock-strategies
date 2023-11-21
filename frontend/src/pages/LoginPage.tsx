import { useState } from 'react';
import { Box, Button, Grid, Link, Paper, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { SHA256 } from 'crypto-js';
import { Copyright } from '../components/Utils';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();


  const handleLogin = (event: any) => {
    event.preventDefault();
    const hashedPassword = SHA256(password).toString();
    fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, hashedPassword })
    })
      .then((res) => {
        if (res.ok) {
          return res.json();
        } else {
          throw new Error('Invalid username or password');
        }
      })
      .then((data) => {
        login({
          fullName: data.fullName,
          email: data.email,
          phoneNumber: data.phoneNumber,
          num_stocks: data.num_stocks,
          investment: data.investment
        });
        navigate('/app');
      })
      .catch((err) => {
        console.error(err);
        alert(err.message);
      });
  };

  const handleSignUp = () => {
    navigate('/register');
  };

  const handleTrialLogin = () => {
    fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: 'trialuser',
        hashedPassword: '79891e980747ffbd21e690297394efe764fa56d7e37750f800879fbb2d34571a'
      })
    }).then((data: any) => {
      login({
        fullName: data.fullName,
        email: data.email,
        phoneNumber: data.phoneNumber,
        num_stocks: data.num_stocks,
        investment: data.investment
      });
      navigate('/app');
    })
      .catch((err) => {
        console.error(err);
        alert(err.message);
      });
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
            <Typography variant="body1" style={{ marginTop: 16, textAlign: 'center' }}>
              Or{' '}
              <Link component="button" variant="body2" onClick={handleTrialLogin}>
                Login as a trial user
              </Link>
            </Typography>
            <Copyright sx={{ mt: 5 }} />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};