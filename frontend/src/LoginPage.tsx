import { useState } from 'react';
import { Button, TextField, Grid, Paper, Typography, Link, Box } from '@material-ui/core';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import CryptoJS from 'crypto-ts';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  

  const handleLogin = (event: any) => {
    event.preventDefault();
    const hashedPassword = CryptoJS.SHA256(password).toString();
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
          id: '1',
          name: username,
          email: 'john.doe@email.com',
          authToken: data.token
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