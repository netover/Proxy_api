/**
 * Heavy Load Test - 400 concurrent users
 * Stress test for high load conditions
 * 
 * Run with: k6 run heavy_load_400_users.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const successCounter = new Counter('successful_requests');
const circuitBreakerTrips = new Counter('circuit_breaker_trips');

export let options = {
    stages: [
        { duration: '2m', target: 100 },   // Ramp up to 100 users
        { duration: '3m', target: 250 },   // Step to 250 users
        { duration: '5m', target: 400 },   // Stay at 400 users
        { duration: '2m', target: 0 },     // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<5000'],   // 95% under 5s
        http_req_failed: ['rate<0.25'],      // Less than 25% failures
        errors: ['rate<0.2'],                // Less than 20% errors
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-key-123';

// Test data for heavy load
const testMessages = [
    "Create a comprehensive business plan for a tech startup",
    "Explain the entire process of building a SaaS application from scratch",
    "Write a detailed technical specification for a distributed system",
    "Describe the architecture of a microservices-based e-commerce platform",
    "Provide a complete guide to implementing authentication and authorization",
    "Explain database design patterns for high-scale applications",
    "Create a performance optimization checklist for web applications",
    "Describe the complete CI/CD pipeline setup for a production application",
    "Write a security audit checklist for web applications",
    "Explain cloud-native application design principles"
];

const models = ['gpt-3.5-turbo', 'claude-3-haiku'];
const maxTokensOptions = [100, 200, 300, 500];

// Distributed load balancing
const endpoints = [
    '/v1/chat/completions',
    '/v1/completions'
];

export default function () {
    group('Heavy Load Test', function () {
        const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
        const model = models[Math.floor(Math.random() * models.length)];
        const maxTokens = maxTokensOptions[Math.floor(Math.random() * maxTokensOptions.length)];
        
        let payload;
        
        if (endpoint === '/v1/chat/completions') {
            payload = JSON.stringify({
                model: model,
                messages: [
                    {
                        role: 'user',
                        content: testMessages[Math.floor(Math.random() * testMessages.length)]
                    }
                ],
                max_tokens: maxTokens,
                temperature: 0.7,
                stream: Math.random() > 0.8,  // 20% streaming requests
                top_p: 0.9
            });
        } else {
            payload = JSON.stringify({
                model: model,
                prompt: testMessages[Math.floor(Math.random() * testMessages.length)],
                max_tokens: maxTokens,
                temperature: 0.8,
                top_p: 0.9
            });
        }

        const params = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
            },
            timeout: 60000, // 60 second timeout for heavy load
        };

        const response = http.post(
            `${BASE_URL}${endpoint}`,
            payload,
            params
        );

        const success = check(response, {
            'status is 200-299': (r) => r.status >= 200 && r.status < 300,
            'response time < 5000ms': (r) => r.timings.duration < 5000,
            'has response content': (r) => {
                try {
                    const body = JSON.parse(r.body);
                    return body.choices && body.choices.length > 0;
                } catch {
                    return false;
                }
            },
        });

        // Check for circuit breaker trips
        const isCircuitBreakerTrip = response.status === 503 || response.status === 429;
        if (isCircuitBreakerTrip) {
            circuitBreakerTrips.add(1);
        }

        errorRate.add(!success);
        responseTime.add(response.timings.duration);
        
        if (success) {
            successCounter.add(1);
        }

        // Aggressive sleep pattern for heavy load
        sleep(Math.random() * 0.5 + 0.1); // 0.1-0.6 seconds between requests
    });

    group('System Health Under Load', function () {
        const responses = http.batch([
            ['GET', `${BASE_URL}/health`],
            ['GET', `${BASE_URL}/metrics`],
            ['GET', `${BASE_URL}/providers`],
        ]);

        check(responses[0], {
            'health check passes under load': (r) => r.status === 200,
            'system remains healthy': (r) => {
                try {
                    const body = JSON.parse(r.body);
                    return body.status === 'healthy' || body.status === 'warning';
                } catch {
                    return false;
                }
            },
        });

        check(responses[1], {
            'metrics endpoint responsive': (r) => r.status === 200,
        });

        check(responses[2], {
            'providers endpoint responsive': (r) => r.status === 200,
        });

        sleep(10);
    });
}

export function handleSummary(data) {
    return {
        'heavy_load_summary.json': JSON.stringify({
            total_requests: data.metrics.http_reqs.values.count,
            successful_requests: data.metrics.successful_requests.values.count,
            failed_requests: data.metrics.http_req_failed.values.count,
            avg_response_time: data.metrics.http_req_duration.values.avg,
            p95_response_time: data.metrics.http_req_duration.values['p(95)'],
            p99_response_time: data.metrics.http_req_duration.values['p(99)'],
            max_response_time: data.metrics.http_req_duration.values.max,
            error_rate: data.metrics.errors.values.rate,
            vus_max: data.metrics.vus_max.values.max,
            circuit_breaker_trips: data.metrics.circuit_breaker_trips.values.count,
            timestamp: Date.now(),
            load_tier: 'heavy_400_users'
        }, null, 2),
    };
}