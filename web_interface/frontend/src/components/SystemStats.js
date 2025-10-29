import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Storage,
  Description,
  Psychology,
  Settings,
  ExpandMore,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';

import { getSystemStats, getDocuments, getConfiguration } from '../services/api';

const SystemStats = () => {
  const [stats, setStats] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsData, docsData, configData] = await Promise.all([
        getSystemStats(),
        getDocuments(),
        getConfiguration()
      ]);
      
      setStats(statsData);
      setDocuments(docsData);
      setConfig(configData);
      setError(null);
    } catch (err) {
      setError('Failed to load system information');
      console.error('Failed to fetch system data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Loading system information...
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      default:
        return 'error';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'operational':
        return <CheckCircle />;
      case 'degraded':
        return <Info />;
      default:
        return <Error />;
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* System Status */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Psychology sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">System Status</Typography>
        </Box>
        
        <Chip
          icon={getStatusIcon(stats?.status)}
          label={stats?.status || 'Unknown'}
          color={getStatusColor(stats?.status)}
          variant="outlined"
          sx={{ mb: 2 }}
        />

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h4" color="primary">
                  {stats?.total_vectors?.toLocaleString() || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Vectors
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h4" color="primary">
                  {stats?.total_documents || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Documents
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Documents */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Description sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">Available Documents</Typography>
        </Box>
        
        {documents.length > 0 ? (
          <List dense>
            {documents.slice(0, 5).map((doc, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <Description fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={doc.title}
                  secondary={`${doc.total_chunks} chunks • ${doc.filename}`}
                />
              </ListItem>
            ))}
            {documents.length > 5 && (
              <ListItem>
                <ListItemText
                  primary={`... and ${documents.length - 5} more documents`}
                  sx={{ fontStyle: 'italic' }}
                />
              </ListItem>
            )}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No documents found
          </Typography>
        )}
      </Paper>

      {/* Configuration */}
      <Paper sx={{ p: 2 }}>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Settings sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Configuration</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {config && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  LLM Configuration
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Model Type"
                      secondary={config.llm_config?.model_type}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Model Name"
                      secondary={config.llm_config?.model_name}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Max Tokens"
                      secondary={config.llm_config?.max_tokens}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Temperature"
                      secondary={config.llm_config?.temperature}
                    />
                  </ListItem>
                </List>

                <Divider sx={{ my: 1 }} />

                <Typography variant="subtitle2" gutterBottom>
                  Embedding Configuration
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Model"
                      secondary={config.embedding_config?.model_name}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Batch Size"
                      secondary={config.embedding_config?.batch_size}
                    />
                  </ListItem>
                </List>

                <Divider sx={{ my: 1 }} />

                <Typography variant="subtitle2" gutterBottom>
                  System Details
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Embedding Dimension"
                      secondary={stats?.embedding_dimension}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Index Location"
                      secondary={stats?.index_location}
                    />
                  </ListItem>
                </List>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      </Paper>
    </Box>
  );
};

export default SystemStats;