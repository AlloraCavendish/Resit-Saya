// Purpose: React entry point — mounts the App component into the DOM.
// Security: Imports global CSS in strict order (tokens → base → layout) and wraps App in StrictMode.

import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/tokens.css';
import './styles/base.css';
import './styles/layout.css';
import App from './App';

// Initialize theme from storage immediately before first render to prevent flicker
try {
  const savedTheme = localStorage.getItem('resitsaya-theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
} catch {
  document.documentElement.setAttribute('data-theme', 'light');
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
