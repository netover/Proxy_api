/**
 * Medium Load Test - 100 concurrent users
 * Moderate performance test for typical load
 *
 * Run with: artillery run medium_load_100_users.test.js
 */

import { check, sleep } from 'artillery';

const testMessages = [
  "What is artificial intelligence?",
  "Explain quantum computing in simple terms",
  "How does machine learning work?",
  "What are the benefits of renewable energy?",
  "Describe the process of photosynthesis"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4', 'claude-3-sonnet'];

export let options = {
  scenarios: [
    {
      name: 'Chat Completion Medium Load',
      engine: 'http',
      weight: 85,
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
              max_tokens: 100,
              temperature: 0.7
            },
            expect: [
              { statusCode: 200 },
              { contentType: 'application/json' },
              { hasProperty: 'choices' }
            ]
          }
        },
        { think: 800 }
      ]
    },
    {
      name: 'Health Check',
      engine: 'http',
      weight: 15,
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
        { think: 1500 }
      ]
    }
  ],
  phases: [
    { duration: 60, arrivalRate: 5, name: 'Ramp up' },
    { duration: 300, arrivalRate: 20, name: 'Medium load' },
    { duration: 60, arrivalRate: 0, name: 'Cool down' }
  ]
};