# 🚀 Quick Start Guide - LLM Proxy API

## 📍 **Access Points & URLs**

### **Application Endpoints**
| Service | URL | Description |
|---------|-----|-------------|
| **Main API** | `http://localhost:8000` | Full API access |
| **Health Check** | `http://localhost:8000/health` | System health status |
| **System Status** | `http://localhost:8000/status` | Detailed system metrics |
| **API Documentation** | `http://localhost:8000/docs` | Swagger UI |
| **OpenAPI Schema** | `http://localhost:8000/openapi.json` | API specification |

### **Observability Dashboards**
| Tool | URL | Purpose |
|------|-----|---------|
| **Jaeger Tracing** | `http://localhost:16686` | Distributed tracing |
| **Zipkin Tracing** | `http://localhost:9411` | Alternative tracing |
| **Prometheus** | `http://localhost:9090` | Metrics (if enabled) |
| **Grafana** | `http://localhost:3000` | Dashboards (if enabled) |

### **Testing Endpoints**
| Endpoint | URL | Method | Description |
|----------|-----|--------|-------------|
| **Chat Completions** | `http://localhost:8000/v1/chat/completions` | POST | Chat-based completions |
| **Text Completions** | `http://localhost:8000/v1/completions` | POST | Text completions |
| **Embeddings** | `http://localhost:8000/v1/embeddings` | POST | Text embeddings |
| **Metrics** | `http://localhost:8000/metrics` | GET | Prometheus metrics |

## 🏃‍♂️ **5-Minute Setup**

### **Step 1: Environment Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Start Jaeger for tracing
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
  -p 16686:16686 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

### **Step 2: Configuration**
```bash
# Set required API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export API_KEY="your-proxy-key"

# Optional configuration
export REDIS_URL="redis://localhost:6379"
export CHAOS_ENGINEERING="false"
```

### **Step 3: Start Application**
```bash
# Normal startup
python main.py

# With chaos engineering
CHAOS_ENGINEERING=true python main.py
```

## 🔗 **Quick API Test**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "model": "gpt-4"
  }'

# Check system status
curl http://localhost:8000/status
```

## 📊 **Verification Commands**
```bash
# Check if services are running
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/status | jq .
curl -s http://localhost:16686/api/services | jq .
```

## 🎯 **Load Testing URLs**
| Test Level | Command | Users | Duration |
|------------|---------|-------|----------|
| **Light** | `k6 run tests/load_tests/light_load_30_users.js` | 30 | 5min |
| **Medium** | `k6 run tests/load_tests/medium_load_100_users.js` | 100 | 5min |
| **Heavy** | `k6 run tests/load_tests/heavy_load_400_users.js` | 400 | 15min |
| **Extreme** | `k6 run tests/load_tests/extreme_load_1000_users.js` | 1000 | 20min |

## 🚨 **Troubleshooting**
- **Service not starting**: Check port 8000 availability
- **No traces in Jaeger**: Ensure Jaeger container is running
- **Redis connection issues**: Verify `redis://localhost:6379` accessibility
- **API key errors**: Check environment variables are set correctly

## 📞 **Support**
For issues accessing these endpoints:
1. Check all services are running: `docker ps`
2. Verify network connectivity: `curl -I http://localhost:8000`
3. Review logs: `docker logs jaeger`
4. Test individual components using the verification commands above