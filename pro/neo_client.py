import json
import time

import requests

from .config import (
    BIONIC_API_KEY,
    BIONIC_ENABLED,
    BIONIC_MODEL,
    BIONIC_URL,
    DEFAULT_CONTEXT_LENGTH,
    LM_STUDIO_AUTH,
    LM_STUDIO_URL,
    MODEL_PRIORITY,
)


class NeoClient:
    def __init__(self):
        self.server_online = False
        self.server_type = None
        self.current_model = None
        self.current_model_name = None
        self.model_available = False
        self.total_context = 0
        self.used_tokens = 0
        self.current_response_id = None
        self.models_list = []
        self.last_stats = {"speed": 0, "tokens": 0, "time": 0}

        self.lmstudio_url = LM_STUDIO_URL
        self.lmstudio_auth = LM_STUDIO_AUTH
        self.bionic_enabled = BIONIC_ENABLED
        self.bionic_url = BIONIC_URL
        self.bionic_api_key = BIONIC_API_KEY
        self.bionic_model = BIONIC_MODEL

    def check_server_status(self):
        if self._check_lmstudio():
            return {
                "status": "online",
                "model": self.current_model_name,
                "context": self.total_context,
                "available_models": self.models_list,
                "server_type": "lmstudio",
            }

        if self.bionic_enabled and self._check_bionic():
            return {
                "status": "online",
                "model": self.current_model_name,
                "context": self.total_context,
                "available_models": self.models_list,
                "server_type": "bionic",
            }

        self.server_online = False
        self.model_available = False
        return {
            "status": "offline",
            "message": "Сервер недоступен или модель не выбрана",
        }

    def _check_lmstudio(self):
        try:
            response = requests.get(
                f"{self.lmstudio_url}/api/v1/models",
                headers={
                    "Authorization": self.lmstudio_auth,
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if response.status_code != 200:
                return False

            data = response.json()
            all_models = data.get("models", [])
            llm_models = [m for m in all_models if m.get("type") == "llm"]
            loaded_model_keys = []
            for model in llm_models:
                if model.get("loaded_instances") and len(model["loaded_instances"]) > 0:
                    loaded_model_keys.append(model["key"])

            found_model_key = None
            found_model_name = None
            for priority in MODEL_PRIORITY:
                if priority["key"] in loaded_model_keys:
                    found_model_key = priority["key"]
                    found_model_name = priority["name"]
                    break

            if not found_model_key and loaded_model_keys:
                found_model_key = loaded_model_keys[0]
                model_info = next(
                    (m for m in llm_models if m["key"] == found_model_key), None
                )
                found_model_name = (
                    model_info.get("display_name") or found_model_key.split("/")[-1]
                    if model_info
                    else found_model_key
                )

            if found_model_key:
                model_info = next(
                    (m for m in llm_models if m["key"] == found_model_key), None
                )
                if model_info and model_info.get("loaded_instances"):
                    instance = model_info["loaded_instances"][0]
                    context_value = instance.get("config", {}).get("context_length")
                    self.total_context = context_value or DEFAULT_CONTEXT_LENGTH
                else:
                    self.total_context = DEFAULT_CONTEXT_LENGTH

                self.server_type = "lmstudio"
                self.current_model = found_model_key
                self.current_model_name = found_model_name
                self.model_available = True
                self.server_online = True
                self.models_list = loaded_model_keys
                return True
            return False
        except (requests.exceptions.RequestException, ValueError, TypeError):
            print("[DEBUG] LM Studio NOT FOUND")
            return False

    def _check_bionic(self):
        print(f"[DEBUG] Checking Bionic at {self.bionic_url}/models")
        if not self.bionic_api_key:
            print("[DEBUG] Bionic API key is empty")
            return False
        try:
            response = requests.get(
                f"{self.bionic_url}/models",
                headers={
                    "Authorization": f"Bearer {self.bionic_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            print(f"[DEBUG] Bionic response status: {response.status_code}")
            if response.status_code != 200:
                print(f"[DEBUG] Bionic response body: {response.text[:200]}")
                return False

            data = response.json()
            models = data.get("data", [])
            if not models:
                return False

            model_ids = [m.get("id") for m in models if m.get("id")]
            if self.bionic_model not in model_ids:
                self.bionic_model = model_ids[0] if model_ids else None
            if not self.bionic_model:
                return False

            self.server_type = "bionic"
            self.current_model = self.bionic_model
            self.current_model_name = self.bionic_model
            self.model_available = True
            self.server_online = True
            self.models_list = model_ids
            self.total_context = DEFAULT_CONTEXT_LENGTH
            return True
        except (requests.exceptions.RequestException, ValueError, TypeError) as e:
            print(f"[DEBUG] Bionic exception: {e}")
            return False

    def send_message_with_preset_stream(self, message, preset_id, reset_context=False):
        if not self.server_online or not self.model_available:
            yield "⚠️ Сервер недоступен или модель не выбрана", "", "error"
            return

        if self.total_context > 0 and self.used_tokens >= self.total_context:
            yield "⚠️ Контекст исчерпан. Начните новый чат.", "", "error"
            return

        if self.server_type == "lmstudio":
            request_body = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": message}],
                "preset": preset_id,
                "store": True,
                "stream": True,
            }
            if not reset_context and self.current_response_id:
                request_body["previous_response_id"] = self.current_response_id
            url = f"{self.lmstudio_url}/v1/chat/completions"
            headers = {
                "Authorization": self.lmstudio_auth,
                "Content-Type": "application/json",
            }
        elif self.server_type == "bionic":
            request_body = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": message}],
                "stream": True,
            }
            url = f"{self.bionic_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.bionic_api_key}",
                "Content-Type": "application/json",
            }
        else:
            yield "⚠️ Неизвестный тип сервера", "", "error"
            return

        start_time = time.time()
        full_content = ""
        full_reasoning = ""
        last_data = None
        tokens_used = 0

        try:
            with requests.post(
                url, headers=headers, json=request_body, stream=True, timeout=600
            ) as response:
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                last_data = data
                                if data.get("choices") and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "reasoning_content" in delta:
                                        full_reasoning += delta["reasoning_content"]
                                    if "content" in delta:
                                        full_content += delta["content"]
                                    yield full_content, full_reasoning, "thinking"
                            except (KeyError, ValueError):
                                data = []

            elapsed = time.time() - start_time

            if last_data and last_data.get("usage"):
                tokens_used = last_data["usage"].get("total_tokens", 0)
                self.used_tokens += tokens_used
            else:
                tokens_used = len(full_content.split()) + len(full_reasoning.split())
                self.used_tokens += tokens_used

            self.last_stats["tokens"] = tokens_used
            self.last_stats["time"] = round(elapsed, 2)
            self.last_stats["speed"] = (
                round(tokens_used / elapsed, 2) if elapsed > 0 else 0
            )

            if (
                self.server_type == "lmstudio"
                and not reset_context
                and last_data
                and last_data.get("response_id")
            ):
                self.current_response_id = last_data["response_id"]

            yield full_content, full_reasoning, "final"

        except requests.RequestException as e:
            yield f"⚠️ Ошибка: {e!s}", "", "error"

    def send_message(self, message, reset_context=False):
        if not self.server_online or not self.model_available:
            return "⚠️ Сервер недоступен или модель не выбрана"

        if self.total_context > 0 and self.used_tokens >= self.total_context:
            return "⚠️ Контекст исчерпан. Начните новый чат."

        if self.server_type == "lmstudio":
            request_body = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": message}],
                "store": True,
            }
            if not reset_context and self.current_response_id:
                request_body["previous_response_id"] = self.current_response_id
            url = f"{self.lmstudio_url}/v1/chat/completions"
            headers = {
                "Authorization": self.lmstudio_auth,
                "Content-Type": "application/json",
            }
        elif self.server_type == "bionic":
            request_body = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": message}],
            }
            url = f"{self.bionic_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.bionic_api_key}",
                "Content-Type": "application/json",
            }
        else:
            return "⚠️ Неизвестный тип сервера"

        try:
            response = requests.post(
                url, headers=headers, json=request_body, timeout=600
            )
            data = response.json()
            if response.status_code == 200:
                if data.get("usage"):
                    tokens_used = data["usage"].get("total_tokens", 0)
                    self.used_tokens += tokens_used
                if not reset_context and data.get("response_id"):
                    self.current_response_id = data["response_id"]
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"].get("content", "")
                    reasoning = data["choices"][0]["message"].get(
                        "reasoning_content", ""
                    )
                    return {"content": content, "reasoning": reasoning}
                return "⚠️ Пустой ответ"
            else:
                error_msg = f"HTTP {response.status_code}"
                if data.get("error"):
                    error_msg = data["error"].get("message", error_msg)
                return f"⚠️ Ошибка: {error_msg}"
        except (KeyError, TypeError, ValueError) as e:
            return f"⚠️ Ошибка: {e}"

    def reset_chat(self):
        self.current_response_id = None
        self.used_tokens = 0

    def get_token_progress(self):
        if self.total_context <= 0:
            return 0, 0, 0
        percentage = (self.used_tokens / self.total_context) * 100
        return self.used_tokens, self.total_context, percentage

    def get_last_stats(self):
        return self.last_stats
