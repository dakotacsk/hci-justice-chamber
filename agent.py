# justice_agents/agent.py
import os
from config import AgentProfile, MODEL_NAME
from memory import ChatMemory

# Attempt to import and configure LLM clients
try:
    import google.generativeai as genai
    genai_available = True
except (ImportError, ModuleNotFoundError, Exception) as e:
    genai = None
    genai_available = False
    # Store error for debugging if needed
    _genai_import_error = str(e)

def get_google_api_key():
    """Get Google API key from environment, checking each time."""
    return os.environ.get("GOOGLE_API_KEY")

def configure_genai():
    """Configure genai with API key if available."""
    if genai_available:
        api_key = get_google_api_key()
        if api_key:
            try:
                genai.configure(api_key=api_key)
                return True
            except Exception:
                return False
    return False




class JusticeAgent:
    def __init__(self, profile: AgentProfile, db_path="./justice_memory.db"):
        self.profile = profile
        self.memory = ChatMemory(db_path)
        self.model_preference = "gemini"  # Default to Gemini

    def _get_llm_client(self):
        """Determines which LLM client to use based on availability."""
        if genai_available:
            api_key = get_google_api_key()
            if api_key:
                # Configure genai if not already configured or if key changed
                try:
                    configure_genai()
                    return genai.GenerativeModel(MODEL_NAME)
                except Exception:
                    return None
        return None

    def _build_context(self, session_id: str) -> list[dict]:
        """Builds a structured history for the LLM prompt."""
        history = self.memory.get_recent(session_id)
        
        # Limit history to the last 2 turns
        recent_history = history[-2:]
        
        # Format for Gemini/OpenAI API
        formatted_history = []
        for m in recent_history:
            # Gemini uses 'user' and 'model', OpenAI uses 'user' and 'assistant'
            role = 'assistant' if m['role'] == 'assistant' else 'user'
            # Prepend agent name for clarity in the context
            content = f"[{m['agent']}]: {m['content']}"
            formatted_history.append({"role": role, "content": content})
            
        return formatted_history

    def generate_response(self, session_id: str, initial_prompt: str = None, max_tokens: int = 100) -> str:
        """Generates a response based on the conversation history."""
        # Check API key dynamically
        api_key = get_google_api_key()
        if not genai_available or not api_key:
            return f"({self.profile.name} is silent as no LLM client is configured.)"

        # Configure genai with the API key
        try:
            configure_genai()
        except Exception as e:
            return f"({self.profile.name} is silent - API configuration error: {e})"

        history = self._build_context(session_id)
        
        # If there's an initial prompt (like the user's first message), add it
        if initial_prompt:
             history.append({"role": "user", "content": f"[User]: {initial_prompt}"})

        try:
            # Gemini uses 'parts' and a different role system
            gemini_history = []
            for turn in history:
                # Gemini uses 'user' for user turns and 'model' for its own turns
                role = 'user' if turn['role'] == 'user' else 'model'
                gemini_history.append({'role': role, 'parts': [turn['content']]})

            model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=self.profile.system_prompt
            )
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens
            )
            response = model.generate_content(
                gemini_history,
                generation_config=generation_config
            )
            if response.candidates:
                reply = response.text.strip()
            else:
                reply = f"({self.profile.name} has no response.)"

        except Exception as e:
            reply = f"({self.profile.name} experiences a moment of reflection... Error: {e})"

        # Add the generated reply to memory
        self.memory.add(session_id, self.profile.name, "assistant", reply)
        return reply

    def end_session(self, session_id: str):
        self.memory.delete_session(session_id)
