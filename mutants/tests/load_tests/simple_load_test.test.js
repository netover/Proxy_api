/**
 * Simple Load Test - Basic performance test
 * Tests the API endpoints with basic load
 *
 * Run with: node simple_load_test.test.js
 */

const http = require('http');

const BASE_URL = 'http://localhost:8000';
const API_KEY = 'test-key-123';
const TEST_DURATION = 30000; // 30 seconds
const CONCURRENT_USERS = 10;
const REQUESTS_PER_SECOND = 5;

const testMessages = [
  "What is artificial intelligence?",
  "Explain quantum computing in simple terms",
  "How does machine learning work?",
  "What are the benefits of renewable energy?",
  "Describe the process of photosynthesis"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4', 'claude-3-sonnet'];

let totalRequests = 0;
let successfulRequests = 0;
let failedRequests = 0;
let responseTimes = [];
let failedResponseTimes = [];
let networkErrorTimes = [];
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

       // Only record timing for successful requests to avoid network bias
       if (res.statusCode === 200) {
         responseTimes.push(responseTime);
         successfulRequests++;
       } else {
         failedRequests++;
         // Record failed request timing separately for analysis
         if (!failedResponseTimes) failedResponseTimes = [];
         failedResponseTimes.push(responseTime);
       }

       totalRequests++;
     });
   });

   req.on('error', (err) => {
     failedRequests++;
     totalRequests++;
     // Record network error timing
     const reqEnd = Date.now();
     const responseTime = reqEnd - reqStart;
     if (!networkErrorTimes) networkErrorTimes = [];
     networkErrorTimes.push(responseTime);
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

console.log('Starting load test...');
console.log(`Duration: ${TEST_DURATION}ms`);
console.log(`Concurrent users: ${CONCURRENT_USERS}`);
console.log(`Requests per second: ${REQUESTS_PER_SECOND}`);
console.log('---');

// Start concurrent users
for (let i = 0; i < CONCURRENT_USERS; i++) {
  setTimeout(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.8) {
        makeHealthCheck();
      } else {
        makeRequest();
      }
    }, 1000 / REQUESTS_PER_SECOND);

    setTimeout(() => {
      clearInterval(interval);
    }, TEST_DURATION);
  }, i * 100); // Stagger user starts
}

// Report results every 5 seconds
const reportInterval = setInterval(() => {
  const elapsed = Date.now() - startTime;
  const avgResponseTime = responseTimes.length > 0 ?
    responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length : 0;
  const rps = totalRequests / (elapsed / 1000);

  console.log(`[${Math.round(elapsed/1000)}s] Requests: ${totalRequests}, Success: ${successfulRequests}, Failed: ${failedRequests}, RPS: ${rps.toFixed(2)}, Avg RT: ${avgResponseTime.toFixed(2)}ms`);
}, 5000);

// Final report
setTimeout(() => {
   clearInterval(reportInterval);

   const totalTime = Date.now() - startTime;
   const avgResponseTime = responseTimes.length > 0 ?
     responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length : 0;
   const minResponseTime = responseTimes.length > 0 ? Math.min(...responseTimes) : 0;
   const maxResponseTime = responseTimes.length > 0 ? Math.max(...responseTimes) : 0;
   const rps = totalRequests / (totalTime / 1000);
   const successRate = totalRequests > 0 ? (successfulRequests / totalRequests) * 100 : 0;

   // Calculate percentiles for better latency analysis
   const sortedTimes = [...responseTimes].sort((a, b) => a - b);
   const p50 = sortedTimes.length > 0 ? sortedTimes[Math.floor(sortedTimes.length * 0.5)] : 0;
   const p95 = sortedTimes.length > 0 ? sortedTimes[Math.floor(sortedTimes.length * 0.95)] : 0;
   const p99 = sortedTimes.length > 0 ? sortedTimes[Math.floor(sortedTimes.length * 0.99)] : 0;

   console.log('\n=== LOAD TEST RESULTS ===');
   console.log(`Total Requests: ${totalRequests}`);
   console.log(`Successful Requests: ${successfulRequests}`);
   console.log(`Failed Requests: ${failedRequests}`);
   console.log(`Success Rate: ${successRate.toFixed(2)}%`);
   console.log(`Requests per Second: ${rps.toFixed(2)}`);
   console.log(`Test Duration: ${totalTime}ms`);
   console.log('');

   console.log('=== RESPONSE TIME ANALYSIS (Successful Requests Only) ===');
   console.log(`Sample Size: ${responseTimes.length} requests`);
   console.log(`Average Response Time: ${avgResponseTime.toFixed(2)}ms`);
   console.log(`Min Response Time: ${minResponseTime}ms`);
   console.log(`Max Response Time: ${maxResponseTime}ms`);
   console.log(`50th Percentile (P50): ${p50.toFixed(2)}ms`);
   console.log(`95th Percentile (P95): ${p95.toFixed(2)}ms`);
   console.log(`99th Percentile (P99): ${p99.toFixed(2)}ms`);

   if (failedResponseTimes && failedResponseTimes.length > 0) {
     const avgFailedTime = failedResponseTimes.reduce((a, b) => a + b, 0) / failedResponseTimes.length;
     console.log(`\nFailed Requests Average Time: ${avgFailedTime.toFixed(2)}ms (${failedResponseTimes.length} samples)`);
   }

   if (networkErrorTimes && networkErrorTimes.length > 0) {
     const avgNetworkErrorTime = networkErrorTimes.reduce((a, b) => a + b, 0) / networkErrorTimes.length;
     console.log(`Network Errors Average Time: ${avgNetworkErrorTime.toFixed(2)}ms (${networkErrorTimes.length} samples)`);
   }

   console.log('\n=== ACCURACY NOTES ===');
   console.log('- Response times exclude network latency for failed requests');
   console.log('- Percentiles provide better latency distribution understanding');
   console.log('- Separate tracking of different failure types for analysis');
   console.log('========================');

   process.exit(0);
}, TEST_DURATION + 1000);