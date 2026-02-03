import requests
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.services import prompts
from dotenv import load_dotenv
from app.core.settings import settings
import logging
import threading

load_dotenv()

class LLMService:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.ollama_model
        self.ollama_url = settings.ollama_url
        self.current_endpoint = settings.ollama_url
        self._checked_models = False
        self._failure_count = 0
        self._cooldown_until: datetime | None = None
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        self._semaphore = threading.Semaphore(settings.llm_max_concurrency)
        self._queue_lock = threading.Lock()
        self._inflight = 0
        self._metrics_lock = threading.Lock()
        self._metrics = {"calls": 0, "batches": 0, "failures": 0}
        self.logger.info("LLM service configured with model %s", self.model_name)
        self.logger.info("LLM endpoint: %s", self.current_endpoint)
        if settings.ollama_shared and "localhost" in self.current_endpoint:
            self.logger.warning("OLLAMA_SHARED is enabled but endpoint is localhost")

    def _maybe_check_models(self) -> None:
        if self._checked_models or not settings.ollama_healthcheck:
            return
        self._checked_models = True

        try:
            response = self.session.get(
                f"{self.current_endpoint}/api/tags",
                timeout=min(settings.ollama_timeout_seconds, 10),
            )
            if response.status_code == 200:
                available_models = [model["name"] for model in response.json().get("models", [])]
                self.logger.info("Ollama available models: %s", available_models)
                if self.model_name not in available_models and available_models:
                    self.logger.warning(
                        "Model %s not found, using %s instead",
                        self.model_name,
                        available_models[0],
                    )
                    self.model_name = available_models[0]
            else:
                self.logger.warning("Ollama tags endpoint returned %s", response.status_code)
        except Exception as e:
            self.logger.warning("Ollama healthcheck failed: %s", e)
    
    def _call_ollama(self, prompt: str, max_tokens: int = 10) -> str:
        """Send a request to Ollama server and get response"""
        self._maybe_check_models()
        if self._cooldown_until and datetime.utcnow() < self._cooldown_until:
            self.logger.warning("LLM cooldown active until %s", self._cooldown_until.isoformat())
            return "unclassified"

        with self._queue_lock:
            if self._inflight >= settings.llm_max_queue:
                self.logger.warning("LLM queue full")
                return "unclassified"
            self._inflight += 1

        acquired = self._semaphore.acquire(timeout=1)
        if not acquired:
            with self._queue_lock:
                self._inflight -= 1
            self.logger.warning("LLM concurrency limit reached")
            return "unclassified"

        try:
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": settings.ollama_temperature,
                    "top_p": settings.ollama_top_p,
                    "num_ctx": 2048,
                }
            }
            
            for attempt in range(settings.ollama_max_retries + 1):
                try:
                    with self._metrics_lock:
                        self._metrics["calls"] += 1
                    self.logger.info("Calling Ollama with model %s (attempt %s)", self.model_name, attempt + 1)
                    response = self.session.post(
                        f"{self.current_endpoint}/api/generate",
                        json=request_data,
                        timeout=(
                            settings.ollama_connect_timeout_seconds,
                            settings.ollama_timeout_seconds,
                        ),
                    )

                    if response.status_code == 200:
                        response_data = response.json()
                        result = response_data.get("response", "").strip()
                        self.logger.info("Received Ollama response")
                        self._failure_count = 0
                        return result

                    self.logger.warning("Ollama API error: status %s", response.status_code)
                except requests.exceptions.Timeout:
                    self.logger.warning("Ollama request timed out")
                except Exception as e:
                    self.logger.error("Error calling Ollama: %s", e)

            self._failure_count += 1
            with self._metrics_lock:
                self._metrics["failures"] += 1
            if self._failure_count >= settings.ollama_failure_threshold:
                self._cooldown_until = datetime.utcnow() + timedelta(seconds=settings.ollama_cooldown_seconds)
                self.logger.warning("LLM cooldown triggered for %s seconds", settings.ollama_cooldown_seconds)
            return "unclassified"
                
        except Exception as e:
            self.logger.error("Unexpected LLM error: %s", e)
            return "unclassified"
        finally:
            self._semaphore.release()
            with self._queue_lock:
                self._inflight -= 1
    
    def extract_topic_from_note(self, note_content: str, note_id: str) -> Dict[str, Any]:
        """Extract a single topic from a note using Ollama"""
        prompt = f"""
        Generate a single general topic (1 word) that best summarizes this note content. It doesn't have to describe the significance of the note as such.
        Choose something more general but not too much. I want a little more generalization because I want to combine some notes into a single topic. But I don't want it too general such that it combines every note.

        Note content:
        {note_content[:2000]}
        
        Return ONLY the topic word, nothing else.
        """
        
        try:
            response = self._call_ollama(prompt, max_tokens=5)
            
            # Clean up the response (sometimes AI adds extra words)
            topic = response.split()[0] if response.split() else "unclassified"
            topic = ''.join(char for char in topic if char.isalnum()).lower()
            
            self.logger.info("Extracted topic '%s' for note %s", topic, note_id)
            return {"topic": topic, "note_id": note_id}
            
        except Exception as e:
            self.logger.error("Error extracting topic for note %s: %s", note_id, e)
            return {"topic": "unclassified", "note_id": note_id}
    
    def process_notes(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process notes and return consolidated topics"""
        self.logger.info("Processing %s notes via Ollama", len(notes))
        
        extracted_topics = []
        for i, note in enumerate(notes):
            self.logger.info("Processing note %s/%s: %s", i + 1, len(notes), note["id"])
            result = self.extract_topic_from_note(note["content"], note["id"])
            extracted_topics.append(result)
        
        # Consolidate duplicate topics
        topic_map = {}
        for item in extracted_topics:
            topic = item["topic"]
            note_id = item["note_id"]
            
            if topic in topic_map:
                topic_map[topic].append(note_id)
            else:
                topic_map[topic] = [note_id]
        
        result = [
            {"topic": topic, "note_ids": note_ids}
            for topic, note_ids in topic_map.items()
        ]
        
        self.logger.info("Consolidated into %s topics", len(result))
        return result

    def extract_topics_batch(self, notes: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        if not notes:
            return []
        with self._metrics_lock:
            self._metrics["batches"] += 1
        prompt = prompts.topic_extraction_prompt(notes)
        response = self._call_ollama(prompt, max_tokens=settings.ollama_max_tokens)
        try:
            data = json.loads(response)
        except Exception:
            return []
        results = []
        for item in data:
            topic = str(item.get("topic", "")).strip().lower()
            note_id = str(item.get("id", "")).strip()
            if topic and note_id:
                results.append({"topic": topic, "note_id": note_id})
        return results

    def healthcheck(self) -> Dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.current_endpoint}/api/tags",
                timeout=min(settings.ollama_timeout_seconds, 5),
            )
            ok = response.status_code == 200
            return {"ok": ok, "status_code": response.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def metrics(self) -> Dict[str, int]:
        with self._metrics_lock:
            return dict(self._metrics)

    def score_relationships_batch(self, pairs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        if not pairs:
            return []
        with self._metrics_lock:
            self._metrics["batches"] += 1
        prompt = prompts.relationship_prompt(pairs)
        response = self._call_ollama(prompt, max_tokens=settings.ollama_max_tokens)
        try:
            data = json.loads(response)
        except Exception:
            return []
        results = []
        for item in data:
            a = str(item.get("a", "")).strip()
            b = str(item.get("b", "")).strip()
            score = item.get("score")
            try:
                score_val = float(score)
            except Exception:
                continue
            if a and b:
                results.append({"a": a, "b": b, "score": max(0.0, min(1.0, score_val))})
        return results

    def set_endpoint(self, endpoint: str) -> None:
        self.current_endpoint = endpoint

    def get_endpoint(self) -> str:
        return self.current_endpoint

# Create a singleton instance
llm_service = LLMService()

# API functions (keeping the same interface for compatibility)
def extract_topics_from_notes(notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of notes and extract consolidated topics.
    
    Args:
        notes: List of dictionaries with note content and IDs
              [{"content": "...", "id": "note1"}, ...]
              
    Returns:
        List of topics with associated note IDs
        [{"topic": "algebra", "note_ids": ["note1", "note3"]}, ...]
    """
    return llm_service.process_notes(notes)

def get_llm_response(prompt: str) -> str:
    """Legacy function for compatibility"""
    try:
        response = llm_service._call_ollama(prompt, max_tokens=100)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

def set_llm_model(model_name: str):
    """Change the AI model being used"""
    llm_service.logger.info("Switching to model: %s", model_name)
    llm_service.model_name = model_name

def get_available_models() -> list:
    """Get list of available Ollama models"""
    try:
        response = llm_service.session.get(
            f"{llm_service.ollama_url}/api/tags",
            timeout=min(settings.ollama_timeout_seconds, 10),
        )
        if response.status_code == 200:
            models_data = response.json()
            return [model["name"] for model in models_data.get("models", [])]
        else:
            return ["llama3.1:8b"]
    except:
        return ["llama3.1:8b"]
