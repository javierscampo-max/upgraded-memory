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
  Snackbar,
  Tabs,
  Tab,
  Box,
  Badge
} from '@mui/material';
import { Science, Chat, Settings, Folder } from '@mui/icons-material';

import ChatInterface from './components/ChatInterface';
import SystemStats from './components/SystemStats';
import RAGManager from './components/RAGManager';
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
  const [currentTab, setCurrentTab] = useState(0);

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

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Tab panel component
  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );

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
            <Badge
              color={systemHealth?.status === 'healthy' ? 'success' : 'error'}
              variant="dot"
              sx={{ mr: 2 }}
            >
              <Typography variant="body2">
                {systemHealth?.status === 'healthy' ? 'Online' : 'Checking...'}
              </Typography>
            </Badge>
          </Toolbar>
          
          {/* Navigation Tabs */}
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            textColor="inherit"
            indicatorColor="secondary"
            sx={{ backgroundColor: 'primary.dark' }}
          >
            <Tab
              icon={<Chat />}
              label="Query Interface"
              sx={{ textTransform: 'none' }}
            />
            <Tab
              icon={<Folder />}
              label="RAG Management"
              sx={{ textTransform: 'none' }}
            />
          </Tabs>
        </AppBar>

        {/* Main Content */}
        <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
          {/* Query Interface Tab */}
          <TabPanel value={currentTab} index={0}>
            <Grid container spacing={3}>
              {/* System Stats */}
              <Grid item xs={12} md={4}>
                <SystemStats />
              </Grid>

              {/* Chat Interface */}
              <Grid item xs={12} md={8}>
                <Paper elevation={2} sx={{ height: 'calc(100vh - 250px)' }}>
                  <ChatInterface />
                </Paper>
              </Grid>
            </Grid>
          </TabPanel>

          {/* RAG Management Tab */}
          <TabPanel value={currentTab} index={1}>
            <RAGManager />
          </TabPanel>
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