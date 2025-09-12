/**
 * Extreme Load Test - 1000 concurrent users
 * Maximum performance test for extreme stress testing
 *
 * Run with: artillery run extreme_load_1000_users.test.js
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
  "Describe climate change impacts",
  "What is machine learning?",
  "Explain deep learning concepts",
  "How does natural language processing work?",
  "What are the applications of AI in healthcare?",
  "Describe the future of autonomous vehicles"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4', 'claude-3-sonnet'];

export let options = {
  scenarios: [
    {
      name: 'Chat Completion Extreme Load',
      engine: 'http',
      weight: 95,
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
              max_tokens: 200,
              temperature: 0.7
            },
            expect: [
              { statusCode: 200 },
              { contentType: 'application/json' },
              { hasProperty: 'choices' }
            ]
          }
        },
        { think: 300 }
      ]
    },
    {
      name: 'Health Check',
      engine: 'http',
      weight: 5,
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
        { think: 500 }
      ]
    }
  ],
  phases: [
    { duration: 600, arrivalRate: 20, name: 'Ramp up' },
    { duration: 1200, arrivalRate: 200, name: 'Extreme load' },
    { duration: 600, arrivalRate: 0, name: 'Cool down' }
  ]
};