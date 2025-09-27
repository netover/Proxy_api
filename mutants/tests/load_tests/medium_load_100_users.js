/**
 * Medium Load Test - 100 concurrent users
 * Moderate load test for sustained performance
 * 
 * Run with: k6 run medium_load_100_users.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const successCounter = new Counter('successful_requests');
const tokenUsage = new Trend('tokens_used');

export let options = {
    stages: [
        { duration: '1m', target: 50 },    // Ramp up to 50 users
        { duration: '3m', target: 100 },   // Stay at 100 users
        { duration: '1m', target: 0 },     // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'],   // 95% under 2s
        http_req_failed: ['rate<0.15'],      // Less than 15% failures
        errors: ['rate<0.1'],                // Less than 10% errors
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-key-123';

// Test data
const testMessages = [
    "Write a Python function to sort a list of dictionaries by a key",
    "Explain the difference between REST and GraphQL APIs",
    "What are the key features of FastAPI?",
    "How do you implement rate limiting in a web application?",
    "Describe the SOLID principles in software design",
    "What is the difference between async and sync programming?",
    "Explain microservices architecture benefits and challenges",
    "How does OAuth2 work?",
    "What are the common security vulnerabilities in web apps?",
    "Describe event-driven architecture"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku', 'gpt-4'];
const maxTokensOptions = [50, 100, 150, 200];

export default function () {
    group('Chat Completion Medium Load', function () {
        const model = models[Math.floor(Math.random() * models.length)];
        const maxTokens = maxTokensOptions[Math.floor(Math.random() * maxTokensOptions.length)];
        
        const payload = JSON.stringify({
            model: model,
            messages: [
                {
                    role: 'user',
                    content: testMessages[Math.floor(Math.random() * testMessages.length)]
                }
            ],
            max_tokens: maxTokens,
            temperature: 0.7,
            stream: Math.random() > 0.7  // 30% streaming requests
        });

        const params = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
            },
            timeout: 30000, // 30 second timeout
        };

        const response = http.post(
            `${BASE_URL}/v1/chat/completions`,
            payload,
            params
        );

        const success = check(response, {
            'status is 200': (r) => r.status === 200,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'has response content': (r) => JSON.parse(r.body).choices && JSON.parse(r.body).choices.length > 0,
            'tokens within limits': (r) => {
                const body = JSON.parse(r.body);
                return body.usage && body.usage.total_tokens <= maxTokens + 100;
            },
        });

        errorRate.add(!success);
        responseTime.add(response.timings.duration);
        
        if (success) {
            successCounter.add(1);
            const body = JSON.parse(response.body);
            if (body.usage) {
                tokenUsage.add(body.usage.total_tokens);
            }
        }

        sleep(Math.random() * 2 + 0.5); // 0.5-2.5 seconds between requests
    });

    group('Text Completion Medium Load', function () {
        const payload = JSON.stringify({
            model: models[Math.floor(Math.random() * models.length)],
            prompt: "Write a brief summary about machine learning:",
            max_tokens: 100,
            temperature: 0.8
        });

        const params = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
            },
            timeout: 30000,
        };

        const response = http.post(
            `${BASE_URL}/v1/completions`,
            payload,
            params
        );

        check(response, {
            'text completion status 200': (r) => r.status === 200,
            'text completion response time < 2000ms': (r) => r.timings.duration < 2000,
        });

        sleep(Math.random() * 2 + 0.5);
    });

    group('Health and Metrics', function () {
        const healthResponse = http.get(`${BASE_URL}/health`);
        const metricsResponse = http.get(`${BASE_URL}/metrics`);

        check(healthResponse, {
            'health check status 200': (r) => r.status === 200,
            'system healthy': (r) => r.json().status === 'healthy',
        });

        check(metricsResponse, {
            'metrics status 200': (r) => r.status === 200,
        });

        sleep(5);
    });
}

export function handleSummary(data) {
    return {
        'medium_load_summary.json': JSON.stringify({
            total_requests: data.metrics.http_reqs.values.count,
            successful_requests: data.metrics.successful_requests.values.count,
            failed_requests: data.metrics.http_req_failed.values.count,
            avg_response_time: data.metrics.http_req_duration.values.avg,
            p95_response_time: data.metrics.http_req_duration.values['p(95)'],
            p99_response_time: data.metrics.http_req_duration.values['p(99)'],
            error_rate: data.metrics.errors.values.rate,
            vus_max: data.metrics.vus_max.values.max,
            avg_tokens_used: data.metrics.tokens_used.values.avg,
            max_tokens_used: data.metrics.tokens_used.values.max,
            timestamp: Date.now()
        }, null, 2),
    };
}