/**
 * Light Load Test - 30 concurrent users
 * Baseline performance test for minimal load
 * 
 * Run with: k6 run light_load_30_users.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const successCounter = new Counter('successful_requests');

export let options = {
    stages: [
        { duration: '30s', target: 10 },   // Ramp up to 10 users
        { duration: '2m', target: 30 },    // Stay at 30 users
        { duration: '30s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<1000'],   // 95% of requests under 1s
        http_req_failed: ['rate<0.1'],       // Less than 10% failures
        errors: ['rate<0.05'],               // Less than 5% errors
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-key-123';

// Test data
const testMessages = [
    "What is artificial intelligence?",
    "Explain quantum computing in simple terms",
    "How does machine learning work?",
    "What are the benefits of renewable energy?",
    "Describe the process of photosynthesis"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4', 'claude-3-sonnet'];

export default function () {
    group('Chat Completion Light Load', function () {
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

        const params = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
            },
        };

        const response = http.post(
            `${BASE_URL}/v1/chat/completions`,
            payload,
            params
        );

        const success = check(response, {
            'status is 200': (r) => r.status === 200,
            'response time < 1000ms': (r) => r.timings.duration < 1000,
            'has response content': (r) => JSON.parse(r.body).choices && JSON.parse(r.body).choices.length > 0,
        });

        errorRate.add(!success);
        responseTime.add(response.timings.duration);
        
        if (success) {
            successCounter.add(1);
        }

        sleep(1); // 1 second between requests
    });

    group('Health Check', function () {
        const response = http.get(`${BASE_URL}/health`);
        
        check(response, {
            'health check status 200': (r) => r.status === 200,
            'health check response time < 500ms': (r) => r.timings.duration < 500,
        });

        sleep(2);
    });
}

export function handleSummary(data) {
    return {
        'light_load_summary.json': JSON.stringify({
            total_requests: data.metrics.http_reqs.values.count,
            successful_requests: data.metrics.successful_requests.values.count,
            failed_requests: data.metrics.http_req_failed.values.count,
            avg_response_time: data.metrics.http_req_duration.values.avg,
            p95_response_time: data.metrics.http_req_duration.values['p(95)'],
            error_rate: data.metrics.errors.values.rate,
            vus_max: data.metrics.vus_max.values.max,
            timestamp: Date.now()
        }, null, 2),
    };
}