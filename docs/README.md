# ProxyAPI Core Modules Documentation

This directory contains comprehensive technical documentation for the core modules of ProxyAPI.

## 📋 Documentation Overview

The [CORE_MODULES_DOCUMENTATION.md](./CORE_MODULES_DOCUMENTATION.md) file provides detailed technical documentation covering:

### 🔗 HTTP Client Implementations
- **V1 HTTP Client (OptimizedHTTPClient)**: Production-ready client with connection pooling and basic retries
- **V2 HTTP Client (AdvancedHTTPClient)**: Advanced client with provider-specific retry strategies and sophisticated error handling
- **Migration Guide**: Complete migration instructions from V1 to V2
- **Performance Characteristics**: Benchmark results and performance comparisons

### 💾 Unified Caching Architecture
- **Cache Interface Protocol**: Standardized interface for all cache implementations
- **Unified Cache Implementation**: Single-layer caching with smart TTL management
- **Cache Strategies**: Intelligent eviction, predictive warming, and consistency monitoring
- **TTL Management**: Dynamic TTL adjustment based on access patterns
- **Monitoring and Metrics**: Comprehensive cache performance monitoring

### 🔐 Authentication System
- **API Key Authentication**: Secure API key verification with timing attack protection
- **Security Best Practices**: Implementation guidelines for secure authentication
- **Rate Limiting Implementation**: Token bucket algorithm with provider-specific limits
- **FastAPI Integration**: Complete integration examples

### ⚙️ Configuration Options
Detailed configuration examples for all core modules including HTTP clients, caching, and authentication.

### 📊 Performance Metrics
Comprehensive performance benchmarks and metrics for all core modules.

### 🛠️ Troubleshooting Guides
Step-by-step troubleshooting procedures for common issues with HTTP clients, caching, and authentication.

### 💻 Code Examples
Complete, runnable code examples demonstrating:
- HTTP client setup and usage
- Advanced cache operations
- Authentication and rate limiting integration
- Monitoring and alerting setup

## 🚀 Key Features Documented

### HTTP Client Features
- Connection pooling and reuse tracking
- Multiple retry strategies (exponential backoff, immediate retry, adaptive)
- Provider-specific configurations
- Circuit breaker integration
- Comprehensive metrics and monitoring

### Caching Features
- Single-layer caching architecture
- Multi-level caching (memory + disk)
- Intelligent TTL management
- Predictive cache warming
- Consistency monitoring and alerting
- Memory-aware operations

### Authentication Features
- Secure API key hashing with SHA-256
- Timing attack protection using `secrets.compare_digest()`
- Token bucket rate limiting
- Provider-specific and route-specific limits
- FastAPI dependency injection integration

## 📈 Performance Improvements

Based on the documentation analysis:

| Component | V1 Performance | V2 Performance | Improvement |
|-----------|----------------|----------------|-------------|
| HTTP Client Success Rate | 93.2% | 94.5% | +1.3% |
| HTTP Client Latency | 245ms | 218ms | -11% |
| Cache Hit Rate | ~80% | ~87% | +7% |
| Memory Usage | 78MB | 72MB | -8% |
| Error Recovery | 30s | 15s | -50% |

## 🔧 Quick Start

1. **HTTP Client**: Use V2 for new implementations with provider-specific retry strategies
2. **Caching**: Enable unified cache with smart TTL and predictive warming
3. **Authentication**: Implement API key authentication with rate limiting
4. **Monitoring**: Set up comprehensive metrics collection and alerting

## 📖 Usage Examples

See the [CORE_MODULES_DOCUMENTATION.md](./CORE_MODULES_DOCUMENTATION.md) file for complete examples including:

- Setting up HTTP clients for different providers
- Configuring unified caching with custom settings
- Implementing secure authentication and rate limiting
- Monitoring and alerting integration

## 🤝 Contributing

When making changes to core modules, ensure:
- Update the corresponding documentation sections
- Include performance benchmarks for new features
- Add troubleshooting guides for new error scenarios
- Update configuration examples for new options

## 📞 Support

For questions about core module implementations, refer to:
1. The detailed code examples in the documentation
2. The troubleshooting guides for common issues
3. The performance metrics for optimization guidance
4. The configuration options for customization