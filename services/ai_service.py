import re
import json
import time
from enum import Enum
from openai import OpenAI

class AIService:
    def __init__(self, settings):
        self.settings = settings
        # Увеличиваем таймаут до 300 секунд (5 минут) для борьбы с 504 Gateway Timeout
        self.client = OpenAI(
            api_key=self.settings.API_KEY,
            base_url=self.settings.BASE_URL,
            timeout=300.0  
        )
        # Динамически получаем список моделей при старте
        self.available_models = self._discover_models()

    def _discover_models(self):
        """Сканирует API для поиска доступных моделей (Self-Discovery)"""
        print("[SYSTEM] Scanning available neural engines...")
        try:
            models_response = self.client.models.list()
            model_ids = [m.id for m in models_response.data]
            
            if not model_ids:
                print("[WARNING] No models found via API! Using emergency fallback.")
                return ["gpt-3.5-turbo"] 
            
            print(f"[SYSTEM] Discovery successful. Found {len(model_ids)} engines: {', '.join(model_ids[:3])}...")
            return model_ids
        except Exception as e:
            print(f"[WARNING] Model discovery failed: {e}. Using emergency fallback.")
            return ["gpt-3.5-turbo"]

    def _validate_prompt(self, topic: str, style: str):
        if not topic or len(topic.strip()) < 3:
            raise ValueError("Topic is too short. Please enter at least 3 characters.")
        if not style:
            raise ValueError("Style is required.")

    def _call_ai(self, model_id: str, system_prompt: str, user_prompt: str) -> str:
        """Низкоуровневый вызов с агрессивным Exponential Backoff для 429, 502, 503, 504"""
        max_retries = 4  # Увеличили количество попыток
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt},
                    ],
                    temperature=0.7,
                    # Включаем JSON mode для максимальной стабильности структуры
                    response_format={"type": "json_object"}
                )
                return (response.choices[0].message.content or '').strip()
            except Exception as e:
                err_msg = str(e)
                print(f"[MODEL: {model_id}] Attempt {attempt} failed: {err_msg}")
                
                # Список ошибок, при которых стоит подождать (Transient Errors)
                is_transient = any(code in err_msg for code in ["429", "502", "503", "504"])

                if is_transient and attempt < max_retries:
                    # Агрессивное ожидание для 5xx ошибок: 15, 30, 60... секунд
                    wait_time = 15 * (2 ** (attempt - 1)) 
                    print(f"[RETRY] Transient error detected ({err_msg}). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                raise e
        
        raise Exception(f"Max retries reached for {model_id}")

    def _run_autopilot(self, system_prompt: str, user_prompt: str) -> str:
        """Цикл перебора моделей для конкретной задачи (Step-level autopilot)"""
        last_error = None
        for model_id in self.available_models:
            print(f"[AUTOPILOT] Trying engine: {model_id}")
            try:
                return self._call_ai(model_id, system_prompt, user_prompt)
            except Exception as e:
                last_error = e
                if isinstance(e, ValueError):
                    raise e
                print(f"[AUTOPILOT] Engine {model_id} is DOWN/BUSY. Error: {e}")
                continue 
        
        raise Exception(f"All available models failed at this step. Last error: {last_error}")

    def generate_content_pipeline(self, topic: str, style: str) -> dict:
        """
        ОПТИМИЗИРОВАННЫЙ КОНВЕЙЕР (SINGLE-PASS MODE).
        Объединен в один запрос для минимизации 429 и 503 ошибок.
        Использует JSON mode для стабильности.
        Учитывает выбранный стиль (Style Integration).
        """
        self._validate_prompt(topic, style)

        print(f"[PIPELINE] Starting optimized single-pass generation for topic: {topic} | Style: {style}")

        # Объединенный промпт с интеграцией стиля
        system_prompt = (
            "You are a professional content strategist and creator. "
            f"Your current style is: '{style}'. "
            f"Adapt your tone, vocabulary, and energy to match the '{style}' style perfectly. "
            "Your task is to generate ideas and then immediately develop the first idea into a full post. "
            "Respond ONLY with a JSON object containing: "
            "'ideas' (a list of 5 short, catchy strings), "
            "'first_idea_details' (an object with 'post_text', 'titles' [list of 3], and 'hashtags' [string]). "
            "STRICT LIMITS: "
            "- 'post_text' must be NO LONGER than 4 short sentences. "
            "- 'hashtags' must be exactly 3 relevant hashtags (e.g., #ai #tech). "
            "- 'titles' must be a list of 3 short titles. "
            "No markdown, no extra text, ONLY raw JSON."
        )
        
        user_prompt = f"Topic: {topic}\\nStyle: {style}"

        raw_json_response = self._run_autopilot(system_prompt, user_prompt)

        try:
            data = json.loads(raw_json_response)
            
            # Извлекаем идеи (для будущего использования в интерфейсе)
            ideas = data.get('ideas', [])
            if not isinstance(ideas, list) or len(ideas) == 0:
                # Fallback если модель забыла про список идей
                ideas = [f"Idea for {topic}"] * 5

            # Извлекаем детали (для текущего вывода)
            details = data.get('first_idea_details', {})
            
            print("[SYSTEM] SUCCESS! Single-pass generation completed.")
            return {
                'topic': topic,
                'style': style,
                'ideas': ideas,
                'post_text': details.get('post_text', ''),
                'titles': details.get('titles', ['Title 1', 'Title 2', 'Title 3']),
                'hashtags': details.get('hashtags', '#content #ai')
            }

        except Exception as e:
            print(f"[PIPELINE] JSON parsing failed: {e}")
            raise ValueError(f"Failed to generate content (Parsing error): {e}")
