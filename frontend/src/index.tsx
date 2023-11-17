import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { App } from './App';
import { LoginPage } from './LoginPage';
import { createRoot } from 'react-dom/client';
import { RegisterPage } from './RegisterPage';
import { useAuth } from './hooks/useAuth';
import { ReactNode } from 'react';
import { AuthContext } from './hooks/AuthContext';
import { User } from './hooks/useUser';
import { createTheme , ThemeProvider, Button } from '@material-ui/core';


const domNode = document.getElementById('root');

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();

  return user ? children : <Navigate to="/login" />;
};

const AppWrapper = () => {
  const [user, setUser] = React.useState<User>();
  const [darkMode, setDarkMode] = React.useState(false);

  const theme = createTheme ({
    palette: {
      type: darkMode ? 'dark' : 'light',
    },
  });

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <AuthContext.Provider value={{ user, setUser }} >

      <Router>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/app" element={

            <ThemeProvider theme={theme}>
              <Button onClick={toggleDarkMode}>
                Toggle Dark Mode
              </Button>
              <ProtectedRoute><App /></ProtectedRoute>
            </ThemeProvider>



          } />

        </Routes>
      </Router>
    </AuthContext.Provider>
  );
};

if (domNode !== null) {
  const root = createRoot(domNode);
  root.render(
    <AppWrapper />
  );
} else {
  console.error("Couldn't find root element");
}