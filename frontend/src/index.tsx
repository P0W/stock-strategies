
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { App } from './App';
import { LoginPage } from './LoginPage';

import { createRoot } from 'react-dom/client';
import { RegisterPage } from './RegisterPage';

const domNode = document.getElementById('root');

if (domNode !== null) {
  const root = createRoot(domNode);

  root.render(
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/app" element={<App />} />
      </Routes>
    </Router>
  );
} else {
  console.error("Couldn't find root element");
}