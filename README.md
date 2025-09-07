# PROXY_API

This is a proxy API for routing requests to different LLM providers, in the style of OpenRouter. It is built with FastAPI.

## Features

*   **OpenAI-compatible endpoint:** `/v1/chat/completions`
*   **Model-based routing:** Routes requests to the appropriate provider based on the requested model.
*   **Provider fallback:** If a request to a provider fails, it will try the next available provider that supports the model.
*   **Configurable providers:** Add and configure providers in `config.yaml`.

## Getting Started

### Prerequisites

*   Python 3.7+
*   pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your API keys:**
    *   Copy the `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your API keys for the providers you want to use.

4.  **Configure your providers:**
    *   Edit the `config.yaml` file to add or remove providers and models.

### Running the application

*   Use `uvicorn` to run the application:
    ```bash
    uvicorn main:app --reload
    ```
*   The API will be available at `http://127.0.0.1:8000`.

## Usage

You can make requests to the `/v1/chat/completions` endpoint using any HTTP client or the OpenAI SDK.

### Example with `curl`

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "gpt-3.5-turbo",
    "messages": [
        {
            "role": "user",
            "content": "Hello!"
        }
    ]
}'
```

### Example with OpenAI Python SDK

```python
import openai

openai.api_base = "http://127.0.0.1:8000/v1"
openai.api_key = "dummy" # The proxy doesn't use this key, but the SDK requires it.

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "Hello!"}
  ]
)

print(response)
```
