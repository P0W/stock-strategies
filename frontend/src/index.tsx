import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { App } from './components/App';
import { LoginPage } from './pages/LoginPage';
import { createRoot } from 'react-dom/client';
import { RegisterPage } from './pages/RegisterPage';
import { useAuth } from './hooks/useAuth';
import { ReactNode } from 'react';
import { AuthContext } from './hooks/AuthContext';
import { User } from './hooks/useUser';
import ProfilePage from './pages/ProfilePage';


const domNode = document.getElementById('root');

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();

  return user ? children : <Navigate to="/login" />;
};

const LoginPageOrRedirect = () => {
  const { user } = useAuth();

  return user ? <Navigate to="/app" /> : <LoginPage />;
};

const AppWrapper = () => {
  const [user, setUser] = React.useState<User>();

  return (
    <AuthContext.Provider value={{ user, setUser }} >
      <Router>
        <Routes>
          <Route path="/" element={<LoginPageOrRedirect />} />
          <Route path="/login" element={<LoginPageOrRedirect />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/app" element={
            <ProtectedRoute><App /></ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
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