import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  CardActions,
  Divider,
  TextField,
  FormControl,
  FormLabel,
  Snackbar,
  Tooltip,
  Badge,
  CircularProgress
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  Warning,
  Refresh,
  Description,
  DeleteSweep,
  Info,
  CheckCircle,
  Error,
  Close,
  Search,
  FilterList,
  Folder,
  InsertDriveFile,
  Build
} from '@mui/icons-material';

import { 
  getRAGFiles, 
  getRAGStats, 
  uploadFiles as apiUploadFiles, 
  deleteFile, 
  rebuildRAGSystem, 
  resetRAGSystem 
} from '../services/api';

const RAGManager = () => {
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ totalFiles: 0, totalVectors: 0, totalSize: 0 });

  // Load files and stats on component mount
  useEffect(() => {
    loadFiles();
    loadStats();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const filesData = await getRAGFiles();
      setFiles(filesData);
    } catch (error) {
      console.error('Failed to load files:', error);
      showNotification('Failed to load files', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await getRAGStats();
      setStats({
        totalFiles: statsData.total_files,
        totalVectors: statsData.total_vectors,
        totalSize: statsData.total_size
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    setSelectedFiles(files);
  }, []);

  const handleDragOver = useCallback((event) => {
    event.preventDefault();
  }, []);

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    
    try {
      const responses = await apiUploadFiles(selectedFiles, (progress) => {
        // Update progress for all files (simplified)
        const newProgress = {};
        selectedFiles.forEach(file => {
          newProgress[file.name] = progress;
        });
        setUploadProgress(newProgress);
      });

      responses.forEach(response => {
        if (response.status === 'success') {
          showNotification(`Successfully uploaded ${response.filename}`, 'success');
        } else {
          showNotification(`Failed to upload ${response.filename}: ${response.message}`, 'error');
        }
      });

      setSelectedFiles([]);
      setUploadProgress({});
      loadFiles();
      loadStats();
    } catch (error) {
      showNotification('Upload failed', 'error');
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = (file) => {
    setFileToDelete(file);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteFile = async () => {
    try {
      await deleteFile(fileToDelete.id);
      showNotification(`Deleted ${fileToDelete.filename}`, 'success');
      setDeleteDialogOpen(false);
      setFileToDelete(null);
      loadFiles();
      loadStats();
    } catch (error) {
      showNotification('Failed to delete file', 'error');
      console.error('Delete error:', error);
    }
  };

  const handleResetRAG = () => {
    setResetDialogOpen(true);
  };

  const handleRebuildRAG = async () => {
    try {
      setLoading(true);
      showNotification('Rebuilding RAG system... This may take a few minutes.', 'info');
      
      const result = await rebuildRAGSystem();
      
      if (result.status === 'success') {
        showNotification('RAG system rebuilt successfully', 'success');
      } else {
        showNotification(`Rebuild failed: ${result.message}`, 'error');
      }
      
      loadFiles();
      loadStats();
    } catch (error) {
      showNotification('Failed to rebuild RAG system', 'error');
      console.error('Rebuild error:', error);
    } finally {
      setLoading(false);
    }
  };

  const confirmResetRAG = async () => {
    try {
      await resetRAGSystem();
      showNotification('RAG system reset successfully', 'success');
      setResetDialogOpen(false);
      loadFiles();
      loadStats();
    } catch (error) {
      showNotification('Failed to reset RAG system', 'error');
      console.error('Reset error:', error);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
  };

  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    file.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <Folder sx={{ mr: 2, fontSize: 32 }} />
        RAG System Management
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">
                {stats.totalFiles}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Documents
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">
                {stats.totalVectors}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Vector Embeddings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">
                {formatFileSize(stats.totalSize)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Size
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* File Upload Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Upload Documents
            </Typography>
            
            <Box
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              sx={{
                border: '2px dashed',
                borderColor: 'primary.main',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                backgroundColor: 'action.hover',
                cursor: 'pointer',
                mb: 2
              }}
              onClick={() => document.getElementById('file-input').click()}
            >
              <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="body1" gutterBottom>
                Drag and drop files here or click to browse
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supported formats: PDF, TXT, DOCX
              </Typography>
            </Box>

            <input
              id="file-input"
              type="file"
              multiple
              accept=".pdf,.txt,.docx"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {selectedFiles.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Selected Files ({selectedFiles.length}):
                </Typography>
                {selectedFiles.map((file, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <InsertDriveFile sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" sx={{ flex: 1 }}>
                      {file.name} ({formatFileSize(file.size)})
                    </Typography>
                    {uploadProgress[file.name] !== undefined && (
                      <Box sx={{ width: 100, ml: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={uploadProgress[file.name]}
                        />
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
            )}

            <Button
              variant="contained"
              startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
              onClick={uploadFiles}
              disabled={selectedFiles.length === 0 || uploading}
              fullWidth
            >
              {uploading ? 'Uploading...' : `Upload ${selectedFiles.length} File(s)`}
            </Button>
          </Paper>

          {/* System Actions */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Actions
            </Typography>
            
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => { loadFiles(); loadStats(); }}
              sx={{ mr: 2, mb: 2 }}
            >
              Refresh Data
            </Button>

            <Button
              variant="contained"
              color="primary"
              startIcon={<Build />}
              onClick={handleRebuildRAG}
              disabled={loading}
              sx={{ mr: 2, mb: 2 }}
            >
              Rebuild RAG
            </Button>

            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteSweep />}
              onClick={handleResetRAG}
              sx={{ mb: 2 }}
            >
              Reset RAG System
            </Button>

            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Resetting the RAG system will remove all documents and embeddings. This action cannot be undone.
              </Typography>
            </Alert>
          </Paper>
        </Grid>

        {/* Files List Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ flex: 1 }}>
                Uploaded Documents ({filteredFiles.length})
              </Typography>
              <TextField
                size="small"
                placeholder="Search files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : filteredFiles.length === 0 ? (
              <Box sx={{ textAlign: 'center', p: 4 }}>
                <Description sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  {searchTerm ? 'No files match your search' : 'No documents uploaded yet'}
                </Typography>
              </Box>
            ) : (
              <List>
                {filteredFiles.map((file) => (
                  <ListItem key={file.id} divider>
                    <ListItemIcon>
                      <Description color={file.processed ? 'primary' : 'disabled'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body1" sx={{ flex: 1 }}>
                            {file.title || file.filename}
                          </Typography>
                          <Chip
                            size="small"
                            label={`${file.vector_count} vectors`}
                            color="primary"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {file.filename} • {formatFileSize(file.size)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Uploaded: {formatDate(file.upload_date)}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Tooltip title="Delete file">
                        <IconButton
                          edge="end"
                          onClick={() => handleDeleteFile(file)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <Warning sx={{ mr: 1, color: 'warning.main' }} />
          Delete Document
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{fileToDelete?.filename}"? 
            This will remove the document and all its associated embeddings.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmDeleteFile} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Confirmation Dialog */}
      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <Warning sx={{ mr: 1, color: 'error.main' }} />
          Reset RAG System
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            This action will permanently delete ALL documents and embeddings.
          </Alert>
          <Typography>
            Are you sure you want to reset the entire RAG system? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmResetRAG} color="error" variant="contained">
            Reset System
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RAGManager;