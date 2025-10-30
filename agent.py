# justice_agents/agent.py
import os
from config import AgentProfile, MODEL_NAME
from memory import ChatMemory

# Attempt to import and configure LLM clients
try:
    import google.generativeai as genai
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
except (ImportError, Exception):
    genai = None
    GOOGLE_API_KEY = None

try:
    import openai
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except (ImportError, Exception):
    openai = None
    OPENAI_API_KEY = None


class JusticeAgent:
    def __init__(self, profile: AgentProfile, db_path="./justice_memory.db"):
        self.profile = profile
        self.memory = ChatMemory(db_path)
        self.model_preference = "gemini"  # Default to Gemini

    def _get_llm_client(self):
        """Determines which LLM client to use based on availability."""
        if self.model_preference == "gemini" and genai and GOOGLE_API_KEY:
            return genai.GenerativeModel(MODEL_NAME)
        elif openai and OPENAI_API_KEY:
            # Fallback to OpenAI if Gemini is not available/configured
            return "openai"
        else:
            return None

    def _build_context(self, session_id: str) -> list[dict]:
        """Builds a structured history for the LLM prompt."""
        history = self.memory.get_recent(session_id)
        
        # Limit history to the last 12 turns
        recent_history = history[-12:]
        
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
        client = self._get_llm_client()
        if not client:
            return f"({self.profile.name} is silent as no LLM client is configured.)"

        history = self._build_context(session_id)
        
        # If there's an initial prompt (like the user's first message), add it
        if initial_prompt:
             history.append({"role": "user", "content": f"[User]: {initial_prompt}"})

        try:
            if self.model_preference == "gemini" and client != "openai":
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
                reply = response.text.strip()
            
            elif client == "openai":
                messages = [{"role": "system", "content": self.profile.system_prompt}]
                messages.extend(history)
                
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens,
                )
                reply = response.choices[0].message.content.strip()
            else:
                 reply = f"({self.profile.name} has no configured LLM.)"

        except Exception as e:
            reply = f"({self.profile.name} experiences a moment of reflection... Error: {e})"

        # Add the generated reply to memory
        self.memory.add(session_id, self.profile.name, "assistant", reply)
        return reply

    def end_session(self, session_id: str):
        self.memory.delete_session(session_id)