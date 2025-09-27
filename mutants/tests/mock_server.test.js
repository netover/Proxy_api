/**
 * Mock Server for Load Testing
 * Simple Express server that mimics the LLM Proxy API endpoints
 *
 * Run with: node mock_server.test.js
 */

const express = require('express');
const app = express();
const port = 8000;

app.use(express.json());

// Mock API key validation
const validApiKeys = ['test-key-123', 'prod-key-456', 'admin-key-789'];

function validateApiKey(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const apiKey = authHeader.substring(7); // Remove 'Bearer ' prefix
  if (!validApiKeys.includes(apiKey)) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  next();
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '2.0.0'
  });
});

// Chat completions endpoint
app.post('/v1/chat/completions', validateApiKey, (req, res) => {
  const { model, messages, max_tokens = 100, temperature = 0.7 } = req.body;

  // Simulate processing delay (50-200ms)
  const delay = Math.random() * 150 + 50;

  setTimeout(() => {
    // Mock response
    const response = {
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: model || 'gpt-3.5-turbo',
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: `This is a mock response for: "${messages[0]?.content || 'No message'}"`
          },
          finish_reason: 'stop'
        }
      ],
      usage: {
        prompt_tokens: messages[0]?.content?.length || 10,
        completion_tokens: max_tokens,
        total_tokens: (messages[0]?.content?.length || 10) + max_tokens
      }
    };

    res.json(response);
  }, delay);
});

// Error simulation endpoint (for chaos testing)
app.post('/v1/chat/completions/error', validateApiKey, (req, res) => {
  // Randomly return different error types
  const errorTypes = [
    { status: 429, message: 'Rate limit exceeded' },
    { status: 500, message: 'Internal server error' },
    { status: 503, message: 'Service temporarily unavailable' },
    { status: 502, message: 'Bad gateway' }
  ];

  const randomError = errorTypes[Math.floor(Math.random() * errorTypes.length)];

  setTimeout(() => {
    res.status(randomError.status).json({
      error: {
        message: randomError.message,
        type: 'api_error',
        code: randomError.status
      }
    });
  }, Math.random() * 1000 + 500);
});

app.listen(port, () => {
  console.log(`Mock LLM Proxy API server running on http://localhost:${port}`);
  console.log('Available endpoints:');
  console.log('  GET  /health');
  console.log('  POST /v1/chat/completions');
  console.log('  POST /v1/chat/completions/error (for chaos testing)');
});