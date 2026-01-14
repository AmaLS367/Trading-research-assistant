import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import App from './App';
import { ThemeProvider } from '@/lib/theme';
import { DocsProvider } from '@/lib/docs-context';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <ThemeProvider>
        <DocsProvider>
          <App />
        </DocsProvider>
      </ThemeProvider>
    </HashRouter>
  </React.StrictMode>
);
