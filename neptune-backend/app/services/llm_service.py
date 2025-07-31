import os
import requests
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self, model_name="llama3.1:8b"):
        self.model_name = model_name
        self.ollama_url = os.getenv("OLLAMA_URL", "http://100.122.73.92:11434")
        print(f"Initializing LLM service with model: {model_name}")
        print(f"Connecting to Ollama at: {self.ollama_url}")
        
        # Test
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                available_models = [model["name"] for model in response.json().get("models", [])]
                print(f"Ollama is running! Available models: {available_models}")
                
                # Check if our preferred model is available
                if model_name not in available_models:
                    print(f"Model {model_name} not found. Available: {available_models}")
                    if available_models:
                        self.model_name = available_models[0]
                        print(f"Using {self.model_name} instead")
            else:
                print("Ollama is running but may have issues")
        except Exception as e:
            print(f"Cannot connect to Ollama server. Error: {e}")
            print("Make sure your server is running and accessible via Tailscale")
    
    def _call_ollama(self, prompt: str, max_tokens: int = 10) -> str:
        """Send a request to Ollama server and get response"""
        try:
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,
                    "num_ctx": 2048  # Context window
                }
            }
            
            print(f"Calling Ollama with model {self.model_name}...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=120
            )
            
            if response.status_code == 200:
                response_data = response.json()
                result = response_data.get("response", "").strip()
                print(f"Got response: '{result}'")
                return result
            else:
                print(f"Ollama API error: Status {response.status_code}")
                return "unclassified"
                
        except requests.exceptions.Timeout:
            print("Ollama request timed out - Intel Mac might be slow")
            return "unclassified"
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return "unclassified"
    
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
            
            print(f"Extracted topic '{topic}' for note {note_id}")
            return {"topic": topic, "note_id": note_id}
            
        except Exception as e:
            print(f"Error extracting topic for note {note_id}: {e}")
            return {"topic": "unclassified", "note_id": note_id}
    
    def process_notes(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process notes and return consolidated topics"""
        print(f"Processing {len(notes)} notes using Ollama on Intel Mac server...")
        print("Note: This might be slower on Intel Mac, please be patient...")
        
        extracted_topics = []
        for i, note in enumerate(notes):
            print(f"Processing note {i+1}/{len(notes)}: {note['id']}")
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
        
        print(f"Consolidated into {len(result)} topics")
        return result

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
    print(f"Switching to model: {model_name}")
    llm_service.model_name = model_name

def get_available_models() -> list:
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{llm_service.ollama_url}/api/tags")
        if response.status_code == 200:
            models_data = response.json()
            return [model["name"] for model in models_data.get("models", [])]
        else:
            return ["llama3.1:8b"]
    except:
        return ["llama3.1:8b"]