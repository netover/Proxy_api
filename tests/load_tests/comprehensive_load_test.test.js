/**
 * Comprehensive Load Test - Multiple load levels
 * Tests the API endpoints with varying load levels
 *
 * Run with: node comprehensive_load_test.test.js
 */

const http = require('http');

const BASE_URL = 'http://localhost:8000';
const API_KEY = 'test-key-123';

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

const loadLevels = [
  { name: 'Light Load (30 users)', duration: 30000, users: 10, rps: 5 },
  { name: 'Medium Load (100 users)', duration: 30000, users: 30, rps: 15 },
  { name: 'Heavy Load (400 users)', duration: 30000, users: 100, rps: 50 },
  { name: 'Extreme Load (1000 users)', duration: 30000, users: 200, rps: 100 }
];

let currentLoadLevel = 0;
let totalRequests = 0;
let successfulRequests = 0;
let failedRequests = 0;
let responseTimes = [];
let startTime = Date.now();

function makeRequest() {
  const payload = JSON.stringify({
    model: models[Math.floor(Math.random() * models.length)],
    messages: [
      {
        role: 'user',
        content: testMessages[Math.floor(Math.random() * testMessages.length)]
      }
    ],
    max_tokens: 100,
    temperature: 0.7
  });

  const options = {
    hostname: 'localhost',
    port: 8000,
    path: '/v1/chat/completions',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Length': Buffer.byteLength(payload)
    }
  };

  const reqStart = Date.now();

  const req = http.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      const reqEnd = Date.now();
      const responseTime = reqEnd - reqStart;
      responseTimes.push(responseTime);
      totalRequests++;

      if (res.statusCode === 200) {
        successfulRequests++;
      } else {
        failedRequests++;
      }
    });
  });

  req.on('error', (err) => {
    failedRequests++;
    totalRequests++;
  });

  req.write(payload);
  req.end();
}

function makeHealthCheck() {
  const options = {
    hostname: 'localhost',
    port: 8000,
    path: '/health',
    method: 'GET'
  };

  const reqStart = Date.now();

  const req = http.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      const reqEnd = Date.now();
      const responseTime = reqEnd - reqStart;
      responseTimes.push(responseTime);
      totalRequests++;

      if (res.statusCode === 200) {
        successfulRequests++;
      } else {
        failedRequests++;
      }
    });
  });

  req.on('error', (err) => {
    failedRequests++;
    totalRequests++;
  });

  req.end();
}

function runLoadLevel(level) {
  console.log(`\n=== Starting ${level.name} ===`);
  console.log(`Duration: ${level.duration}ms`);
  console.log(`Concurrent users: ${level.users}`);
  console.log(`Requests per second: ${level.rps}`);
  console.log('---');

  // Reset counters for this level
  const levelStartRequests = totalRequests;
  const levelStartTime = Date.now();

  // Start concurrent users
  const intervals = [];
  for (let i = 0; i < level.users; i++) {
    const interval = setTimeout(() => {
      const userInterval = setInterval(() => {
        if (Math.random() > 0.85) { // 15% health checks
          makeHealthCheck();
        } else {
          makeRequest();
        }
      }, 1000 / level.rps);

      intervals.push(userInterval);

      setTimeout(() => {
        clearInterval(userInterval);
      }, level.duration);
    }, i * 50); // Stagger user starts

    intervals.push(interval);
  }

  // Report progress every 5 seconds
  const reportInterval = setInterval(() => {
    const elapsed = Date.now() - levelStartTime;
    const levelRequests = totalRequests - levelStartRequests;
    const avgResponseTime = responseTimes.length > 0 ?
      responseTimes.slice(-100).reduce((a, b) => a + b, 0) / Math.min(100, responseTimes.slice(-100).length) : 0;
    const rps = levelRequests / (elapsed / 1000);

    console.log(`[${Math.round(elapsed/1000)}s] Requests: ${levelRequests}, RPS: ${rps.toFixed(2)}, Avg RT: ${avgResponseTime.toFixed(2)}ms`);
  }, 5000);

  // Move to next level after duration
  setTimeout(() => {
    clearInterval(reportInterval);
    intervals.forEach(clearInterval);

    // Report results for this level
    const levelRequests = totalRequests - levelStartRequests;
    const levelTime = Date.now() - levelStartTime;
    const levelSuccess = successfulRequests - (levelStartRequests - (totalRequests - levelRequests - failedRequests + successfulRequests - levelRequests));
    const levelFailed = failedRequests - (levelStartRequests - levelRequests - levelSuccess);

    const avgResponseTime = responseTimes.length > 0 ?
      responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length : 0;
    const successRate = levelRequests > 0 ? (levelSuccess / levelRequests) * 100 : 0;

    console.log(`\n=== ${level.name} RESULTS ===`);
    console.log(`Total Requests: ${levelRequests}`);
    console.log(`Successful Requests: ${levelSuccess}`);
    console.log(`Failed Requests: ${levelFailed}`);
    console.log(`Success Rate: ${successRate.toFixed(2)}%`);
    console.log(`Average Response Time: ${avgResponseTime.toFixed(2)}ms`);
    console.log(`Requests per Second: ${(levelRequests / (levelTime / 1000)).toFixed(2)}`);
    console.log(`Test Duration: ${levelTime}ms`);

    currentLoadLevel++;
    if (currentLoadLevel < loadLevels.length) {
      setTimeout(() => runLoadLevel(loadLevels[currentLoadLevel]), 2000);
    } else {
      // Final comprehensive report
      setTimeout(() => {
        const totalTime = Date.now() - startTime;
        const avgResponseTime = responseTimes.length > 0 ?
          responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length : 0;
        const minResponseTime = responseTimes.length > 0 ? Math.min(...responseTimes) : 0;
        const maxResponseTime = responseTimes.length > 0 ? Math.max(...responseTimes) : 0;
        const rps = totalRequests / (totalTime / 1000);
        const successRate = totalRequests > 0 ? (successfulRequests / totalRequests) * 100 : 0;

        console.log('\n===============================');
        console.log('COMPREHENSIVE LOAD TEST RESULTS');
        console.log('===============================');
        console.log(`Total Requests: ${totalRequests}`);
        console.log(`Successful Requests: ${successfulRequests}`);
        console.log(`Failed Requests: ${failedRequests}`);
        console.log(`Overall Success Rate: ${successRate.toFixed(2)}%`);
        console.log(`Average Response Time: ${avgResponseTime.toFixed(2)}ms`);
        console.log(`Min Response Time: ${minResponseTime}ms`);
        console.log(`Max Response Time: ${maxResponseTime}ms`);
        console.log(`Overall RPS: ${rps.toFixed(2)}`);
        console.log(`Total Test Duration: ${totalTime}ms`);
        console.log('===============================');

        process.exit(0);
      }, 1000);
    }
  }, level.duration + 1000);
}

console.log('Starting comprehensive load test...');
console.log('Testing multiple load levels sequentially');
runLoadLevel(loadLevels[currentLoadLevel]);