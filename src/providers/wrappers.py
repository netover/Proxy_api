"""
Wrappers e Transformers para compatibilidade OpenAI.
Converte payloads de providers não-OpenAI para formato padrão.
"""

from typing import Dict, List, Callable
from src.core.logging import logger

# A classe base do cliente OpenAI é frequentemente usada para tipagem e compatibilidade.
# Se não estiver disponível, podemos definir uma estrutura similar.
try:
    from openai import AsyncOpenAI
    from openai.types.chat import ChatCompletion
except ImportError:
    logger.warning("openai library not found. Using mock classes for type hinting.")
    AsyncOpenAI = object
    ChatCompletion = object


class GenericOpenAIWrapper:
    """
    Wrapper genérico para providers que são compatíveis com a API OpenAI.
    Isso serve como fallback para qualquer provider no registry que não tenha um wrapper customizado.
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.transformer: Callable[[Dict], Dict] = (
            lambda payload: payload
        )  # Default: no-op

    def set_transformer(self, transformer: Callable[[Dict], Dict]):
        """Aplica um transformador de payload a este wrapper."""
        self.transformer = transformer

    async def chat_completions(
        self, model: str, messages: List[Dict], **kwargs
    ) -> Dict:
        """
        Chama o endpoint /v1/chat/completions.
        O payload é primeiro passado pelo transformer.
        """
        payload = {"model": model, "messages": messages, **kwargs}

        # Aplica a transformação de payload
        transformed_payload = self.transformer(payload)

        try:
            response: ChatCompletion = await self.client.chat.completions.create(
                **transformed_payload
            )
            # Retorna o dicionário para consistência com o formato JSON da API
            return response.model_dump()
        except Exception as e:
            logger.error(f"Erro no wrapper genérico para {self.client.base_url}: {e}")
            raise

    async def embeddings(self, model: str, input: List[str], **kwargs) -> Dict:
        """Chama o endpoint /v1/embeddings."""
        payload = {"model": model, "input": input, **kwargs}
        transformed_payload = self.transformer(payload)

        try:
            response = await self.client.embeddings.create(**transformed_payload)
            return response.model_dump()
        except Exception as e:
            logger.error(
                f"Erro no wrapper de embeddings para {self.client.base_url}: {e}"
            )
            raise


# --- Payload Transformers ---


class AnthropicTransformer:
    """Converte um payload no formato OpenAI para o formato da API da Anthropic."""

    def __call__(self, payload: Dict) -> Dict:
        logger.debug("Applying AnthropicTransformer")
        # Anthropic usa 'system' prompt e tem um formato de 'messages' diferente
        system_prompt = ""
        user_messages = []
        for msg in payload.get("messages", []):
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                user_messages.append(msg)

        payload["messages"] = user_messages
        if system_prompt:
            payload["system"] = system_prompt.strip()

        # Mapeia 'max_tokens' para o parâmetro da Anthropic
        if "max_tokens" in payload:
            payload["max_tokens_to_sample"] = payload.pop("max_tokens")

        return payload


class GoogleTransformer:
    """Converte um payload no formato OpenAI para o formato da Google AI Studio (Gemini)."""

    def __call__(self, payload: Dict) -> Dict:
        logger.debug("Applying GoogleTransformer")
        # Gemini usa 'contents' em vez de 'messages'
        contents = []
        for msg in payload.get("messages", []):
            # O role 'assistant' do OpenAI mapeia para 'model' no Gemini
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload["contents"] = contents

        # Mapeia parâmetros para 'generationConfig'
        generation_config = {
            "temperature": payload.pop("temperature", 0.7),
            "maxOutputTokens": payload.pop("max_tokens", 1024),
            "topP": payload.pop("top_p", 1.0),
        }
        payload["generationConfig"] = generation_config

        # Gemini requer configurações de segurança
        payload["safetySettings"] = [
            {"category": cat, "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            for cat in [
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
            ]
        ]

        # Remove campos que não são do Gemini
        payload.pop("messages", None)
        payload.pop("model", None)

        return payload


class CohereTransformer:
    """Converte um payload no formato OpenAI para o formato da API da Cohere."""

    def __call__(self, payload: Dict) -> Dict:
        logger.debug("Applying CohereTransformer")
        # Cohere usa 'message' para a última mensagem do usuário
        messages = payload.get("messages", [])
        if messages:
            last_msg = messages[-1]
            payload["message"] = last_msg["content"]

            # Constrói o histórico de chat para a Cohere
            chat_history = []
            for msg in messages[:-1]:
                role = "USER" if msg["role"] == "user" else "CHATBOT"
                chat_history.append({"role": role, "message": msg["content"]})
            payload["chat_history"] = chat_history

        # Remove campos que não são da Cohere
        payload.pop("messages", None)

        return payload
