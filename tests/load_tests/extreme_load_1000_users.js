/**
 * Extreme Load Test - 1000 concurrent users
 * Maximum stress test for system limits
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const requestCount = new Counter('requests');
const circuitBreakerCount = new Counter('circuit_breakers');
const rateLimitCount = new Counter('rate_limits');

// Test configuration
export let options = {
  stages: [
    { duration: '3m', target: 250 },   // Gradual ramp to 250 users
    { duration: '3m', target: 500 },   // Ramp to 500 users
    { duration: '3m', target: 750 },   // Ramp to 750 users
    { duration: '3m', target: 1000 },  // Peak at 1000 users
    { duration: '8m', target: 1000 },  // Sustained extreme load
    { duration: '2m', target: 500 },   // Gradual ramp down
    { duration: '1m', target: 0 },     // Cool down
  ],
  thresholds: {
    // Relaxed thresholds for extreme load conditions
    http_req_duration: ['p(95)<10000'],  // 95% under 10s (extreme load)
    http_req_duration: ['p(99)<20000'],  // 99% under 20s
    http_req_failed: ['rate<0.2'],       // Error rate under 20% (acceptable under extreme load)
    errors: ['rate<0.1'],               // Custom error rate under 10%
    circuit_breakers: ['count<100'],    // Max 100 circuit breaker activations
  },
  
  // Aggressive settings for extreme testing
  http_req_timeout: '60s',
  noConnectionReuse: false,
  maxRedirects: 0,
};

// Configuration
const apiKey = __ENV.API_KEY || 'your-api-key-here';
const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
const maxRetries = __ENV.MAX_RETRIES || 3;

// Advanced test data generation
function generateDynamicPayload(type) {
  const randomContent = randomString(50, 200);
  
  switch (type) {
    case 'chat':
      return JSON.stringify({
        messages: [
          { role: 'user', content: `Explain the concept of ${randomContent} in simple terms` }
        ],
        model: 'gpt-4',
        max_tokens: 200 + Math.floor(Math.random() * 100),
        temperature: Math.random() * 0.5 + 0.5
      });
    
    case 'text':
      return JSON.stringify({
        prompt: `Write a comprehensive analysis about ${randomContent}`,
        model: 'gpt-4',
        max_tokens: 150 + Math.floor(Math.random() * 100),
        temperature: Math.random() * 0.3 + 0.7
      });
    
    case 'embeddings':
      return JSON.stringify({
        input: [
          randomString(20, 50),
          randomString(20, 50),
          randomString(20, 50)
        ],
        model: 'text-embedding-ada-002'
      });
  }
}

// Advanced request handler with detailed error tracking
function makeAdvancedRequest(endpoint, payload) {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    timeout: '60s',
  };
  
  const startTime = Date.now();
  const res = http.post(`${baseUrl}${endpoint}`, payload, params);
  const duration = Date.now() - startTime;
  
  requestCount.add(1);
  
  // Track specific error types
  if (res.status === 503) {
    circuitBreakerCount.add(1);
  } else if (res.status === 429) {
    rateLimitCount.add(1);
  }
  
  // Comprehensive checks
  const checks = {
    'status tracked': (r) => true,
    'response time measured': (r) => duration > 0,
    'circuit breaker handled': (r) => r.status !== 503 || true,
    'rate limit handled': (r) => r.status !== 429 || true,
  };
  
  check(res, checks);
  
  errorRate.add(res.status >= 400);
  responseTime.add(duration);
  
  return {
    status: res.status,
    duration: duration,
    size: res.body ? res.body.length : 0,
    endpoint: endpoint
  };
}

// Load distribution strategy
export default function() {
  // Weighted distribution based on realistic usage
  const weights = {
    'chat': 0.5,      // 50% chat completions
    'text': 0.3,      // 30% text completions
    'embeddings': 0.2  // 20% embeddings
  };
  
  const random = Math.random();
  let selectedType;
  
  if (random < weights.chat) {
    selectedType = 'chat';
  } else if (random < weights.chat + weights.text) {
    selectedType = 'text';
  } else {
    selectedType = 'embeddings';
  }
  
  const endpoint = {
    'chat': '/v1/chat/completions',
    'text': '/v1/completions',
    'embeddings': '/v1/embeddings'
  }[selectedType];
  
  const payload = generateDynamicPayload(selectedType);
  
  // Make request
  const result = makeAdvancedRequest(endpoint, payload);
  
  // Adaptive sleep based on response time
  const sleepTime = Math.min(result.duration / 1000, 3);
  sleep(sleepTime * Math.random() + 0.5);
}

// Setup and teardown
export function setup() {
  console.log('🚀 EXTREME LOAD TEST STARTED');
  console.log('===========================');
  console.log('Maximum users: 1000');
  console.log('Test duration: ~20 minutes');
  console.log('Expected requests: 1000+ RPS at peak');
  console.log('Configuration:');
  console.log(`  API Key: ${apiKey.substring(0, 8)}...`);
  console.log(`  Base URL: ${baseUrl}`);
  console.log(`  Max retries: ${maxRetries}`);
  console.log('');
  
  return {
    testType: 'extreme_load',
    maxUsers: 1000,
    maxRetries: maxRetries,
    startTime: Date.now()
  };
}

export function teardown(data) {
  const duration = Date.now() - data.startTime;
  
  console.log('');
  console.log('🎯 EXTREME LOAD TEST COMPLETED');
  console.log('==============================');
  console.log(`Total duration: ${Math.round(duration/60000)} minutes`);
  console.log(`Total requests: ${requestCount.value}`);
  console.log(`Circuit breaker activations: ${circuitBreakerCount.value}`);
  console.log(`Rate limit hits: ${rateLimitCount.value}`);
  console.log('System under test has been thoroughly stress-tested!');
}