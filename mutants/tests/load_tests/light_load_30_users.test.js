/**
 * Light Load Test - 30 concurrent users
 * Baseline performance test for minimal load
 *
 * Run with: artillery run light_load_30_users.test.js
 */

export let options = {
  target: 'http://localhost:8000',
  scenarios: [
    {
      name: 'Chat Completion Light Load',
      engine: 'http',
      weight: 80,
      flow: [
        {
          post: {
            url: '/v1/chat/completions',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer test-key-123'
            },
            json: {
              model: 'gpt-3.5-turbo',
              messages: [
                {
                  role: 'user',
                  content: 'What is artificial intelligence?'
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
        { think: 1000 }
      ]
    },
    {
      name: 'Health Check',
      engine: 'http',
      weight: 20,
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
        { think: 2000 }
      ]
    }
  ],
  phases: [
    { duration: 30, arrivalRate: 1, name: 'Warm up' },
    { duration: 120, arrivalRate: 5, name: 'Light load' },
    { duration: 30, arrivalRate: 0, name: 'Cool down' }
  ]
};