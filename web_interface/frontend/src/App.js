import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Alert,
  Snackbar
} from '@mui/material';
import { Science, Chat } from '@mui/icons-material';

import ChatInterface from './components/ChatInterface';
import SystemStats from './components/SystemStats';
import { checkHealth } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check system health on startup
    const checkSystemHealth = async () => {
      try {
        const health = await checkHealth();
        setSystemHealth(health);
      } catch (err) {
        setError('Failed to connect to the RAG system. Please ensure the backend is running.');
        console.error('Health check failed:', err);
      }
    };

    checkSystemHealth();
    
    // Check health every 30 seconds
    const interval = setInterval(checkSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleErrorClose = () => {
    setError(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
        {/* App Bar */}
        <AppBar position="static" elevation={1}>
          <Toolbar>
            <Science sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Scientific Papers RAG Query System
            </Typography>
            <Chat sx={{ mr: 1 }} />
            <Typography variant="body2">
              {systemHealth?.status === 'healthy' ? 'Online' : 'Checking...'}
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
          <Grid container spacing={3}>
            {/* System Stats */}
            <Grid item xs={12} md={4}>
              <SystemStats />
            </Grid>

            {/* Chat Interface */}
            <Grid item xs={12} md={8}>
              <Paper elevation={2} sx={{ height: 'calc(100vh - 200px)' }}>
                <ChatInterface />
              </Paper>
            </Grid>
          </Grid>
        </Container>

        {/* Error Snackbar */}
        <Snackbar 
          open={!!error} 
          autoHideDuration={6000} 
          onClose={handleErrorClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleErrorClose} severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        </Snackbar>
      </div>
    </ThemeProvider>
  );
}

export default App;