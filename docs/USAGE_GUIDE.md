# 📖 Usage Guide - LLM Proxy API

Complete guide with practical examples, tutorials, and use cases for the LLM Proxy API.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Advanced Examples](#advanced-examples)
- [Integration Tutorials](#integration-tutorials)
- [Use Case Examples](#use-case-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Basic Chat Completion

```python
import requests

# Basic chat completion
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer your-api-key",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello! How are you?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
)

print(response.json())
```

### 2. Model Discovery

```python
# Discover available models
models_response = requests.get(
    "http://localhost:8000/api/models",
    headers={"Authorization": "Bearer your-api-key"}
)

models = models_response.json()["models"]
print(f"Available models: {len(models)}")

# Filter by provider
openai_models = [m for m in models if m["provider"] == "openai"]
print(f"OpenAI models: {len(openai_models)}")
```

### 3. Streaming Response

```python
# Streaming chat completion
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer your-api-key",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Tell me a story"}],
        "stream": True,
        "max_tokens": 500
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data != '[DONE]':
                chunk = json.loads(data)
                content = chunk['choices'][0]['delta'].get('content', '')
                print(content, end='', flush=True)
```

## Basic Usage

### Authentication

```python
# API Key authentication
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

# All requests require authentication
response = requests.get("http://localhost:8000/api/models", headers=headers)
```

### Chat Completions

#### Simple Chat

```python
def chat_completion(message, model="gpt-3.5-turbo", max_tokens=150):
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
    )
    return response.json()

# Usage
result = chat_completion("Explain quantum computing in simple terms")
print(result["choices"][0]["message"]["content"])
```

#### Multi-turn Conversation

```python
def chat_with_history(messages, model="gpt-4"):
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.8
        }
    )
    return response.json()

# Usage
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user", "content": "What's interesting about it?"}
]

result = chat_with_history(conversation)
print(result["choices"][0]["message"]["content"])
```

#### Function Calling

```python
def chat_with_functions(message, functions):
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": message}],
            "functions": functions,
            "function_call": "auto"
        }
    )
    return response.json()

# Define functions
functions = [
    {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
]

# Usage
result = chat_with_functions("What's the weather in Tokyo?", functions)
print(result)
```

### Model Management

#### List Available Models

```python
def get_available_models():
    response = requests.get(
        "http://localhost:8000/api/models",
        headers={"Authorization": "Bearer your-api-key"}
    )
    return response.json()

# Get all models
models_data = get_available_models()
print(f"Total models: {models_data['count']}")

# Filter models
chat_models = [m for m in models_data["models"] if m["supports_chat"]]
vision_models = [m for m in models_data["models"] if "vision" in m.get("capabilities", [])]

print(f"Chat models: {len(chat_models)}")
print(f"Vision models: {len(vision_models)}")
```

#### Search Models

```python
def search_models(query, **filters):
    params = {"q": query}
    params.update(filters)

    response = requests.get(
        "http://localhost:8000/api/models/search",
        headers={"Authorization": "Bearer your-api-key"},
        params=params
    )
    return response.json()

# Search by name
gpt4_models = search_models("gpt-4")
print(f"GPT-4 models: {len(gpt4_models['models'])}")

# Advanced search
advanced_results = search_models(
    "claude",
    provider="anthropic",
    supports_chat=True,
    min_context=100000
)
print(f"Advanced search results: {len(advanced_results['models'])}")
```

#### Get Model Details

```python
def get_model_details(model_id):
    response = requests.get(
        f"http://localhost:8000/api/models/{model_id}",
        headers={"Authorization": "Bearer your-api-key"}
    )
    return response.json()

# Get specific model info
gpt4_info = get_model_details("gpt-4")
print(f"Model: {gpt4_info['model']['name']}")
print(f"Context: {gpt4_info['model']['context_length']}")
print(f"Input cost: ${gpt4_info['model']['input_cost']}/1K tokens")
```

## Advanced Examples

### Context Condensation

```python
def condense_context(messages, max_tokens=512):
    """Condense long conversation context"""
    response = requests.post(
        "http://localhost:8000/api/condense",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "messages": messages,
            "max_tokens": max_tokens
        }
    )
    return response.json()

# Usage with long conversation
long_conversation = [
    {"role": "user", "content": "Tell me about Python programming"},
    {"role": "assistant", "content": "Python is a high-level programming language..."},
    # ... many more messages
]

condensed = condense_context(long_conversation)
print(f"Condensed context: {condensed['summary']}")
```

### Asynchronous Processing

```python
async def async_chat_completion(message):
    """Asynchronous chat completion"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/v1/chat/completions",
            headers={
                "Authorization": "Bearer your-api-key",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 200
            }
        ) as response:
            return await response.json()

# Usage
import asyncio
result = asyncio.run(async_chat_completion("Explain async programming"))
print(result)
```

### Batch Processing

```python
def batch_chat_completions(requests_list):
    """Process multiple chat requests in batch"""
    responses = []

    for req in requests_list:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={
                "Authorization": "Bearer your-api-key",
                "Content-Type": "application/json"
            },
            json=req
        )
        responses.append(response.json())

    return responses

# Usage
batch_requests = [
    {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Summarize this article..."}],
        "max_tokens": 100
    },
    {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Analyze this code..."}],
        "max_tokens": 200
    }
]

results = batch_chat_completions(batch_requests)
for i, result in enumerate(results):
    print(f"Request {i+1}: {result['choices'][0]['message']['content'][:50]}...")
```

### Error Handling and Retry

```python
def robust_chat_completion(message, max_retries=3):
    """Chat completion with robust error handling"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/v1/chat/completions",
                headers={
                    "Authorization": "Bearer your-api-key",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 150
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited, wait and retry
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"API error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            continue
        except requests.exceptions.ConnectionError:
            print(f"Connection error on attempt {attempt + 1}")
            continue

    print("Max retries exceeded")
    return None

# Usage
result = robust_chat_completion("Hello, world!")
if result:
    print(result["choices"][0]["message"]["content"])
```

## Integration Tutorials

### Web Application Integration

```python
# Flask web application with LLM Proxy
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

LLM_PROXY_URL = "http://localhost:8000"
API_KEY = "your-api-key"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'gpt-3.5-turbo')

    try:
        response = requests.post(
            f"{LLM_PROXY_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 200
            }
        )

        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "response": result["choices"][0]["message"]["content"]
            })
        else:
            return jsonify({
                "success": False,
                "error": f"API error: {response.status_code}"
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
```

### Discord Bot Integration

```python
# Discord bot with LLM Proxy
import discord
import requests
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

LLM_PROXY_URL = "http://localhost:8000"
API_KEY = "your-api-key"

@bot.command(name='ask')
async def ask(ctx, *, question):
    """Ask the AI a question"""
    async with ctx.typing():
        try:
            response = requests.post(
                f"{LLM_PROXY_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": question}],
                    "max_tokens": 300
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                await ctx.send(f"🤖 {answer}")
            else:
                await ctx.send("❌ Sorry, I couldn't get a response right now.")

        except requests.exceptions.Timeout:
            await ctx.send("⏰ The request timed out. Please try again.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name='models')
async def list_models(ctx):
    """List available models"""
    try:
        response = requests.get(
            f"{LLM_PROXY_URL}/api/models",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        if response.status_code == 200:
            models_data = response.json()
            models = models_data["models"][:10]  # Show first 10

            embed = discord.Embed(
                title="Available Models",
                description=f"Showing {len(models)} of {models_data['count']} models"
            )

            for model in models:
                embed.add_field(
                    name=model["name"],
                    value=f"Provider: {model['provider']}\nContext: {model['context_length']}",
                    inline=True
                )

            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Could not fetch models.")

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

bot.run('your-bot-token')
```

### Slack Integration

```python
# Slack app with LLM Proxy
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests

app = App(token="your-slack-bot-token")

LLM_PROXY_URL = "http://localhost:8000"
API_KEY = "your-api-key"

@app.event("app_mention")
def handle_mention(event, say):
    """Handle @bot mentions"""
    text = event["text"].replace(f"<@{event['user']}>", "").strip()

    if not text:
        say("Hello! Ask me anything.")
        return

    try:
        # Get AI response
        response = requests.post(
            f"{LLM_PROXY_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 300
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]

            # Send response
            say(f"<@{event['user']}> {answer}")
        else:
            say(f"<@{event['user']}> Sorry, I couldn't process your request.")

    except requests.exceptions.Timeout:
        say(f"<@{event['user']}> The request timed out. Please try again.")
    except Exception as e:
        say(f"<@{event['user']}> An error occurred: {str(e)}")

@app.command("/ask-ai")
def handle_slash_command(ack, respond, command):
    """Handle /ask-ai slash command"""
    ack()

    question = command["text"]
    if not question:
        respond("Please provide a question after /ask-ai")
        return

    try:
        response = requests.post(
            f"{LLM_PROXY_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": question}],
                "max_tokens": 200
            }
        )

        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            respond(answer)
        else:
            respond("Sorry, I couldn't get a response.")

    except Exception as e:
        respond(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, "your-app-token")
    handler.start()
```

## Use Case Examples

### Content Generation

```python
def generate_blog_post(topic, tone="professional", length="medium"):
    """Generate a blog post on a given topic"""

    # Define length parameters
    length_map = {
        "short": 300,
        "medium": 600,
        "long": 1000
    }
    max_tokens = length_map.get(length, 600)

    prompt = f"""
    Write a {tone} blog post about: {topic}

    The post should be engaging, informative, and well-structured with:
    - An attention-grabbing introduction
    - Main content with key points
    - A conclusion with actionable insights
    - SEO-friendly elements

    Length: approximately {max_tokens} words
    """

    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
    )

    result = response.json()
    return result["choices"][0]["message"]["content"]

# Usage
post = generate_blog_post("The Future of AI in Healthcare", tone="informative", length="long")
print(post)
```

### Code Review Assistant

```python
def review_code(code_snippet, language="python"):
    """AI-powered code review"""

    prompt = f"""
    Please review the following {language} code and provide:
    1. Overall assessment
    2. Potential bugs or issues
    3. Performance considerations
    4. Best practices suggestions
    5. Security concerns (if any)

    Code to review:
    ```{language}
    {code_snippet}
    ```

    Please be specific and constructive in your feedback.
    """

    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.3
        }
    )

    result = response.json()
    return result["choices"][0]["message"]["content"]

# Usage
code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

review = review_code(code, "python")
print("Code Review:")
print(review)
```

### Data Analysis Assistant

```python
def analyze_dataset_description(description, analysis_type="summary"):
    """Analyze dataset based on description"""

    analysis_prompts = {
        "summary": "Provide a comprehensive summary of this dataset",
        "insights": "Extract key insights and patterns from this dataset description",
        "visualization": "Suggest appropriate visualizations for this dataset",
        "quality": "Assess the quality and potential issues of this dataset"
    }

    prompt = f"""
    {analysis_prompts.get(analysis_type, analysis_prompts['summary'])}

    Dataset Description:
    {description}

    Please provide detailed, actionable analysis.
    """

    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={
            "Authorization": "Bearer your-api-key",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
            "temperature": 0.4
        }
    )

    result = response.json()
    return result["choices"][0]["message"]["content"]

# Usage
dataset_desc = """
This dataset contains customer purchase history from an e-commerce platform.
It includes 1 million records with fields: customer_id, purchase_date,
product_category, purchase_amount, customer_location, and payment_method.
The data spans 2 years from 2022-2023.
"""

analysis = analyze_dataset_description(dataset_desc, "insights")
print("Dataset Analysis:")
print(analysis)
```

### Customer Support Chatbot

```python
class SupportChatbot:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.api_key = "your-api-key"
        self.conversation_history = []

    def initialize_conversation(self):
        """Set up the initial system prompt"""
        self.conversation_history = [{
            "role": "system",
            "content": """
            You are a helpful customer support assistant for TechCorp.
            Be friendly, professional, and concise in your responses.
            If you don't know something, admit it and offer to escalate.
            Always try to solve the customer's problem efficiently.

            Company policies:
            - Refunds within 30 days
            - 24/7 technical support
            - Premium support for enterprise customers
            """
        }]

    def chat(self, user_message):
        """Process user message and get AI response"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Get AI response
        response = requests.post(
            f"{self.api_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": self.conversation_history,
                "max_tokens": 300,
                "temperature": 0.7,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1
            }
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]

            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })

            return ai_response
        else:
            return "I'm sorry, I'm having trouble connecting to our support system. Please try again later."

    def get_conversation_summary(self):
        """Get a summary of the conversation"""
        summary_prompt = "Please provide a brief summary of this customer support conversation:"

        summary_response = requests.post(
            f"{self.api_url}/api/condense",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "messages": self.conversation_history,
                "max_tokens": 100
            }
        )

        if summary_response.status_code == 200:
            return summary_response.json().get("summary", "Summary not available")
        else:
            return "Unable to generate summary"

# Usage
bot = SupportChatbot()
bot.initialize_conversation()

# Simulate conversation
responses = []
responses.append(bot.chat("Hi, I can't access my account"))
responses.append(bot.chat("I forgot my password"))
responses.append(bot.chat("Can you help me reset it?"))

print("Conversation:")
for i, response in enumerate(responses, 1):
    print(f"Bot {i}: {response}")

print(f"\nSummary: {bot.get_conversation_summary()}")
```

## Best Practices

### API Usage

1. **Error Handling**
   ```python
   # Always handle API errors gracefully
   try:
       response = requests.post(url, json=data, headers=headers, timeout=30)
       response.raise_for_status()  # Raise exception for bad status codes
       result = response.json()
   except requests.exceptions.Timeout:
       print("Request timed out")
   except requests.exceptions.ConnectionError:
       print("Connection error")
   except requests.exceptions.HTTPError as e:
       print(f"HTTP error: {e}")
   except json.JSONDecodeError:
       print("Invalid JSON response")
   ```

2. **Rate Limiting**
   ```python
   # Implement client-side rate limiting
   import time
   from collections import deque

   class RateLimiter:
       def __init__(self, requests_per_minute=60):
           self.requests_per_minute = requests_per_minute
           self.requests = deque()

       def can_make_request(self):
           now = time.time()
           # Remove old requests
           while self.requests and now - self.requests[0] > 60:
               self.requests.popleft()

           return len(self.requests) < self.requests_per_minute

       def record_request(self):
           self.requests.append(time.time())

   rate_limiter = RateLimiter()

   if rate_limiter.can_make_request():
       # Make API request
       response = requests.post(url, json=data, headers=headers)
       rate_limiter.record_request()
   else:
       print("Rate limit exceeded, please wait")
   ```

3. **Request Optimization**
   ```python
   # Use appropriate parameters for your use case
   optimized_request = {
       "model": "gpt-3.5-turbo",  # Choose appropriate model
       "messages": messages,
       "max_tokens": min(estimated_tokens * 1.2, 4000),  # Estimate tokens needed
       "temperature": 0.7,  # Adjust for creativity vs consistency
       "top_p": 0.9,  # Nucleus sampling
       "frequency_penalty": 0.1,  # Reduce repetition
       "presence_penalty": 0.1,  # Encourage topic diversity
       "stop": ["\n\n", "###"]  # Custom stop sequences
   }
   ```

### Performance Optimization

1. **Caching Strategy**
   ```python
   # Cache frequently used responses
   import hashlib

   def get_cache_key(messages, model, **params):
       """Generate cache key for request"""
       content = f"{model}:{messages}:{params}"
       return hashlib.md5(content.encode()).hexdigest()

   def cached_completion(messages, model="gpt-3.5-turbo", use_cache=True):
       if use_cache:
           cache_key = get_cache_key(messages, model)
           # Check cache first
           cached_result = cache.get(cache_key)
           if cached_result:
               return cached_result

       # Make API request
       result = chat_completion(messages, model)

       if use_cache:
           # Cache the result
           cache.set(cache_key, result, ttl=3600)

       return result
   ```

2. **Batch Processing**
   ```python
   # Process multiple requests efficiently
   def batch_process(requests, batch_size=5):
       results = []

       for i in range(0, len(requests), batch_size):
           batch = requests[i:i + batch_size]

           # Process batch concurrently
           with ThreadPoolExecutor(max_workers=batch_size) as executor:
               batch_results = list(executor.map(process_single_request, batch))

           results.extend(batch_results)

           # Small delay between batches to respect rate limits
           time.sleep(1)

       return results
   ```

3. **Connection Reuse**
   ```python
   # Reuse HTTP connections
   session = requests.Session()

   def make_request(url, data):
       with session.post(url, json=data, headers=headers) as response:
           return response.json()

   # Session automatically reuses connections
   ```

### Cost Optimization

1. **Model Selection**
   ```python
   # Choose cost-effective models
   def select_model(requirements):
       models = get_available_models()

       # Filter by requirements
       suitable_models = [
           m for m in models
           if m["supports_chat"] and
           m["context_length"] >= requirements.get("min_context", 4000)
       ]

       # Sort by cost (input cost + output cost)
       suitable_models.sort(key=lambda m: m["input_cost"] + m["output_cost"])

       return suitable_models[0] if suitable_models else None
   ```

2. **Token Optimization**
   ```python
   # Optimize token usage
   def optimize_prompt(prompt, max_tokens=4000):
       """Optimize prompt to fit within token limit"""
       # Estimate tokens (rough approximation)
       estimated_tokens = len(prompt.split()) * 1.3

       if estimated_tokens > max_tokens * 0.8:
           # Summarize or truncate prompt
           summary_prompt = f"Summarize the following text in {max_tokens // 4} words or less:\n\n{prompt}"

           summary = chat_completion([{"role": "user", "content": summary_prompt}],
                                   max_tokens=max_tokens // 4)

           return summary["choices"][0]["message"]["content"]

       return prompt
   ```

## Troubleshooting

### Common Issues

#### Authentication Errors

**Problem:** `401 Unauthorized` or `403 Forbidden`
```python
# Check API key
response = requests.get("http://localhost:8000/api/models",
                       headers={"Authorization": "Bearer your-api-key"})
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

#### Rate Limiting

**Problem:** `429 Too Many Requests`
```python
# Check rate limit headers
response = requests.post(url, json=data, headers=headers)
print(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining')}")
print(f"Rate limit reset: {response.headers.get('X-RateLimit-Reset')}")

# Implement exponential backoff
import time
wait_time = 2 ** attempt  # Exponential backoff
time.sleep(wait_time)
```

#### Timeout Issues

**Problem:** Request timeouts
```python
# Increase timeout
response = requests.post(url, json=data, headers=headers, timeout=60)

# Or use streaming for long responses
response = requests.post(url, json={**data, "stream": True},
                        headers=headers, stream=True)
```

#### Model Not Found

**Problem:** `404 Model not found`
```python
# Check available models
models = requests.get("http://localhost:8000/api/models").json()
available_models = [m["id"] for m in models["models"]]
print(f"Available models: {available_models}")

# Use a valid model ID
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add request debugging
response = requests.post(url, json=data, headers=headers)
print(f"Request URL: {response.request.url}")
print(f"Request headers: {response.request.headers}")
print(f"Request body: {response.request.body}")
print(f"Response status: {response.status_code}")
print(f"Response headers: {response.headers}")
```

### Health Checks

```python
# Check API health
health = requests.get("http://localhost:8000/health").json()
print(f"API Status: {health['status']}")

# Check provider status
providers = requests.get("http://localhost:8000/health/providers").json()
for provider, status in providers.items():
    print(f"{provider}: {status}")

# Check cache status
cache_status = requests.get("http://localhost:8000/health/cache").json()
print(f"Cache status: {cache_status}")
```

---

**📖 This comprehensive usage guide provides practical examples and tutorials for effectively using the LLM Proxy API across various scenarios and integrations.**