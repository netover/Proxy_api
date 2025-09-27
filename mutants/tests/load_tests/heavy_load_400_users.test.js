/**
 * Heavy Load Test - 400 concurrent users
 * High performance test for stress testing
 *
 * Run with: artillery run heavy_load_400_users.test.js
 */

import { check, sleep } from 'artillery';

const testMessages = [
  "What is artificial intelligence?",
  "Explain quantum computing in simple terms",
  "How does machine learning work?",
  "What are the benefits of renewable energy?",
  "Describe the process of photosynthesis",
  "What is the theory of relativity?",
  "How do vaccines work?",
  "Explain blockchain technology",
  "What are neural networks?",
  "Describe climate change impacts"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4', 'claude-3-sonnet'];

export let options = {
  scenarios: [
    {
      name: 'Chat Completion Heavy Load',
      engine: 'http',
      weight: 90,
      flow: [
        {
          post: {
            url: '/v1/chat/completions',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer test-key-123'
            },
            json: {
              model: models[Math.floor(Math.random() * models.length)],
              messages: [
                {
                  role: 'user',
                  content: testMessages[Math.floor(Math.random() * testMessages.length)]
                }
              ],
              max_tokens: 150,
              temperature: 0.7
            },
            expect: [
              { statusCode: 200 },
              { contentType: 'application/json' },
              { hasProperty: 'choices' }
            ]
          }
        },
        { think: 500 }
      ]
    },
    {
      name: 'Health Check',
      engine: 'http',
      weight: 10,
      flow: [
        {
          get: {
            url: '/health',
            expect: [
              { statusCode: 200 },
              { contentType: 'application/json' }
            ]
          }
        },
        { think: 1000 }
      ]
    }
  ],
  phases: [
    { duration: 300, arrivalRate: 10, name: 'Ramp up' },
    { duration: 600, arrivalRate: 80, name: 'Heavy load' },
    { duration: 300, arrivalRate: 0, name: 'Cool down' }
  ]
};