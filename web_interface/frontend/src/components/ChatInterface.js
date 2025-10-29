import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Chip,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Alert,
  Slider,
  FormControl,
  FormLabel,
  Divider,
  Pagination,
  ToggleButtonGroup,
  ToggleButton,
  Tooltip,
  Badge,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Send,
  ExpandMore,
  Person,
  SmartToy,
  Description,
  AccessTime,
  Settings,
  ViewCompact,
  ViewList,
  Search,
  FilterList,
  ExpandLess,
  Star
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

import { queryRAGSystem } from '../services/api';

// Enhanced Sources Display Component for scalability
const SourcesDisplay = ({ sources, maxHeight = '300px' }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [viewMode, setViewMode] = useState('compact'); // 'compact' or 'detailed'
  const [searchTerm, setSearchTerm] = useState('');
  const [showAll, setShowAll] = useState(false);
  
  const SOURCES_PER_PAGE = 10;
  const HIGH_RELEVANCE_THRESHOLD = 0.8; // Adjust based on your scoring system
  
  // Filter sources based on search term
  const filteredSources = sources.filter(source =>
    source.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    source.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Group sources by relevance
  const highRelevanceSources = filteredSources.filter(s => s.similarity_score >= HIGH_RELEVANCE_THRESHOLD);
  const regularSources = filteredSources.filter(s => s.similarity_score < HIGH_RELEVANCE_THRESHOLD);
  
  // Calculate pagination
  const totalPages = Math.ceil(filteredSources.length / SOURCES_PER_PAGE);
  const startIndex = (currentPage - 1) * SOURCES_PER_PAGE;
  const paginatedSources = filteredSources.slice(startIndex, startIndex + SOURCES_PER_PAGE);
  
  const getRelevanceColor = (score) => {
    if (score >= HIGH_RELEVANCE_THRESHOLD) return 'success';
    if (score >= 0.6) return 'warning';
    return 'default';
  };
  
  const getRelevanceIcon = (score) => {
    if (score >= HIGH_RELEVANCE_THRESHOLD) return <Star fontSize="small" />;
    return <Description fontSize="small" />;
  };
  
  const renderSourceItem = (source, index, compact = false) => (
    <Box
      key={index}
      sx={{
        p: compact ? 1 : 1.5,
        mb: 1,
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        backgroundColor: source.similarity_score >= HIGH_RELEVANCE_THRESHOLD ? 'success.50' : 'background.paper'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: compact ? 0.5 : 1 }}>
        {getRelevanceIcon(source.similarity_score)}
        <Typography
          variant={compact ? "caption" : "body2"}
          fontWeight="bold"
          sx={{ ml: 1, flex: 1 }}
          noWrap={compact}
        >
          {source.title}
        </Typography>
        <Chip
          size="small"
          label={source.similarity_score?.toFixed(3)}
          color={getRelevanceColor(source.similarity_score)}
        />
      </Box>
      <Typography 
        variant="caption" 
        color="text.secondary"
        sx={{ display: 'block', pl: compact ? 0 : 3 }}
      >
        {source.filename}
      </Typography>
    </Box>
  );
  
  return (
    <Box>
      {/* Header with controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
        <Description sx={{ color: 'primary.main' }} />
        <Typography variant="body2" sx={{ flex: 1 }}>
          Sources ({sources.length})
          {highRelevanceSources.length > 0 && (
            <Chip
              size="small"
              icon={<Star />}
              label={`${highRelevanceSources.length} highly relevant`}
              color="success"
              sx={{ ml: 1 }}
            />
          )}
        </Typography>
        
        {sources.length > 10 && (
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="compact">
              <Tooltip title="Compact view">
                <ViewCompact fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="detailed">
              <Tooltip title="Detailed view">
                <ViewList fontSize="small" />
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>
        )}
      </Box>
      
      {/* Search bar for many sources */}
      {sources.length > 5 && (
        <TextField
          size="small"
          placeholder="Search sources..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1); // Reset pagination on search
          }}
          InputProps={{
            startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ width: '100%', mb: 2 }}
        />
      )}
      
      {/* Sources container with scrolling */}
      <Box
        sx={{
          maxHeight: sources.length > 20 ? maxHeight : 'auto',
          overflowY: sources.length > 20 ? 'auto' : 'visible',
          overflowX: 'hidden'
        }}
      >
        {filteredSources.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
            No sources match your search
          </Typography>
        ) : (
          <>
            {/* High relevance sources first (if any and not too many) */}
            {highRelevanceSources.length > 0 && highRelevanceSources.length <= 5 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="success.main" sx={{ fontWeight: 'bold', mb: 1, display: 'block' }}>
                  HIGHLY RELEVANT
                </Typography>
                {highRelevanceSources.map((source, index) => renderSourceItem(source, `high-${index}`, viewMode === 'compact'))}
                {regularSources.length > 0 && <Divider sx={{ my: 1 }} />}
              </Box>
            )}
            
            {/* Paginated display for many sources */}
            {filteredSources.length > SOURCES_PER_PAGE ? (
              <>
                {paginatedSources.map((source, index) => 
                  renderSourceItem(source, startIndex + index, viewMode === 'compact')
                )}
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={totalPages}
                    page={currentPage}
                    onChange={(e, page) => setCurrentPage(page)}
                    size="small"
                    color="primary"
                  />
                </Box>
              </>
            ) : (
              /* Show all for reasonable numbers */
              (regularSources.length <= 5 || highRelevanceSources.length <= 5 ? 
                filteredSources : 
                (highRelevanceSources.length > 5 ? highRelevanceSources.concat(regularSources) : filteredSources)
              ).map((source, index) => renderSourceItem(source, index, viewMode === 'compact'))
            )}
          </>
        )}
      </Box>
      
      {/* Summary for very large numbers */}
      {sources.length > 50 && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 1 }}>
          Showing {Math.min(filteredSources.length, SOURCES_PER_PAGE)} of {filteredSources.length} sources
          {searchTerm && ` (filtered from ${sources.length} total)`}
        </Typography>
      )}
    </Box>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [k, setK] = useState(5); // Number of documents to retrieve
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentQuestion.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: currentQuestion,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentQuestion('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await queryRAGSystem(currentQuestion, k);
      
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.answer,
        sources: response.sources,
        processingTime: response.processing_time,
        timestamp: response.timestamp
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError('Failed to get response. Please try again.');
      console.error('Query failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" gutterBottom>
          Ask about Scientific Papers
        </Typography>
        
        {/* Settings */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Settings fontSize="small" />
          <FormControl sx={{ minWidth: 200 }}>
            <FormLabel>Relevant chunks to include: {k}</FormLabel>
            <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', mb: 1 }}>
              Most similar document chunks to send as context
            </Box>
            <Slider
              value={k}
              onChange={(e, newValue) => setK(newValue)}
              min={1}
              max={200}
              marks={[
                { value: 1, label: '1' },
                { value: 50, label: '50' },
                { value: 100, label: '100' },
                { value: 150, label: '150' },
                { value: 200, label: '200' }
              ]}
              size="small"
            />
          </FormControl>
        </Box>
      </Box>

      {/* Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {messages.length === 0 && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <SmartToy sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Welcome to the RAG Query System
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask questions about the scientific papers in your knowledge base.
            </Typography>
          </Box>
        )}

        {messages.map((message) => (
          <Box key={message.id} sx={{ mb: 2 }}>
            {message.type === 'user' ? (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Card sx={{ maxWidth: '70%', bgcolor: 'primary.main', color: 'white' }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Person sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="body2" sx={{ opacity: 0.8 }}>
                        You • {formatTimestamp(message.timestamp)}
                      </Typography>
                    </Box>
                    <Typography variant="body1">{message.content}</Typography>
                  </CardContent>
                </Card>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                <Card sx={{ maxWidth: '85%' }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <SmartToy sx={{ mr: 1, fontSize: 20, color: 'primary.main' }} />
                      <Typography variant="body2" color="text.secondary">
                        Assistant • {formatTimestamp(message.timestamp)}
                      </Typography>
                      {message.processingTime && (
                        <Chip
                          icon={<AccessTime />}
                          label={`${message.processingTime}s`}
                          size="small"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </Box>

                    {message.sources && message.sources.length > 0 && (
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Description sx={{ mr: 1 }} />
                            <Typography variant="body2">
                              Retrieved Sources ({message.sources.length})
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <SourcesDisplay sources={message.sources} maxHeight="400px" />
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        ))}

        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Card sx={{ maxWidth: '70%' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
                <CircularProgress size={20} sx={{ mr: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Processing your question...
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Error Alert */}
      {error && (
        <Box sx={{ p: 2 }}>
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <form onSubmit={handleSubmit}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Ask a question about the scientific papers..."
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              disabled={isLoading}
              multiline
              maxRows={3}
            />
            <IconButton
              type="submit"
              disabled={isLoading || !currentQuestion.trim()}
              color="primary"
              sx={{ alignSelf: 'flex-end' }}
            >
              <Send />
            </IconButton>
          </Box>
        </form>
      </Box>
    </Box>
  );
};

export default ChatInterface;