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
  Divider
} from '@mui/material';
import {
  Send,
  ExpandMore,
  Person,
  SmartToy,
  Description,
  AccessTime,
  Settings
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

import { queryRAGSystem } from '../services/api';

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
                              Sources ({message.sources.length})
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          {message.sources.map((source, index) => (
                            <Box key={index} sx={{ mb: 1 }}>
                              <Typography variant="body2" fontWeight="bold">
                                {source.title}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {source.filename} • Score: {source.similarity_score?.toFixed(3)}
                              </Typography>
                            </Box>
                          ))}
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