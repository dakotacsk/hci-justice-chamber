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

    def _build_context(self, session_id: str, max_turns: int = 30) -> list[dict]:
        """Builds a structured history for the LLM prompt.
        
        Args:
            session_id: The session identifier
            max_turns: Maximum number of conversation turns to include (default: 30)
                      If history exceeds this, older messages are truncated while
                      preserving recent context.
        """
        history = self.memory.get_recent(session_id)
        
        # If history is too long, truncate while preserving recent context
        # Keep the most recent max_turns messages
        if len(history) > max_turns:
            # Keep first message (if exists) for context, then recent messages
            # This helps maintain conversation flow
            if len(history) > max_turns + 1:
                # Keep first message and last max_turns-1 messages
                recent_history = [history[0]] + history[-(max_turns-1):]
            else:
                recent_history = history[-max_turns:]
        else:
            recent_history = history
        
        # Format for Gemini/OpenAI API
        formatted_history = []
        for m in recent_history:
            # Gemini uses 'user' for user turns and 'model' for assistant turns
            role = 'assistant' if m['role'] == 'assistant' else 'user'
            
            # Format content based on role
            if m['role'] == 'user':
                # User messages: just the content
                content = m['content']
            else:
                # Agent messages: format clearly to show who said what
                # Use a format that's clear but doesn't encourage copying
                if m['agent'] == self.profile.name:
                    # For the current agent's own messages, just use the content
                    # (they know it's from them)
                    content = m['content']
                else:
                    # For other agents, use a format that distinguishes speakers
                    # but is less likely to be copied verbatim
                    content = f"Note: {m['agent']} previously mentioned: {m['content']}"
            
            formatted_history.append({"role": role, "content": content})
            
        return formatted_history

    def generate_response(self, session_id: str, initial_prompt: str = None, max_tokens: int = 100) -> str:
        """Generates a response based on the conversation history.
        
        Uses the full conversation history from memory to provide context-aware responses.
        For multi-agent conversations, each agent sees all messages from all participants.
        """
        # Check API key dynamically
        api_key = get_google_api_key()
        if not genai_available or not api_key:
            return f"({self.profile.name} is silent as no LLM client is configured.)"

        # Configure genai with the API key
        try:
            configure_genai()
        except Exception as e:
            return f"({self.profile.name} is silent - API configuration error: {e})"

        # Build context from memory (includes all agents' messages)
        history = self._build_context(session_id, max_turns=30)
        
        # If there's an initial prompt (like the user's first message), add it
        if initial_prompt:
             history.append({"role": "user", "content": initial_prompt})

        try:
            # Convert history to Gemini format
            # Gemini uses 'parts' and a different role system
            gemini_history = []
            for turn in history:
                # Gemini uses 'user' for user turns and 'model' for assistant turns
                role = 'user' if turn['role'] == 'user' else 'model'
                gemini_history.append({'role': role, 'parts': [turn['content']]})

            # Enhance system prompt to clarify the agent should respond as themselves
            enhanced_system_prompt = f"""{self.profile.system_prompt}

IMPORTANT: You are {self.profile.name}. When you respond, speak directly as yourself. Do not include agent name prefixes like "[Agent Name]:" in your responses. Simply respond naturally as {self.profile.name}."""
            
            model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=enhanced_system_prompt
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
                # Remove any agent name prefixes that might have been included in the response
                # This prevents issues where the LLM copies the format from conversation history
                import re
                # Remove patterns like "[Agent Name]:" from the start (common format issue)
                # Match brackets with agent names followed by colon
                reply = re.sub(r'^\[[^\]]+\]:\s*', '', reply)
                # Remove patterns like "Agent Name said:" from the start
                reply = re.sub(r'^[^:]+ said:\s*', '', reply)
                # Remove "Another participant" patterns - handle nested parentheses in agent names
                reply = re.sub(r'^Another participant[^:]*said:\s*', '', reply, flags=re.IGNORECASE)
                # Remove "Note: Agent Name previously mentioned:" pattern
                reply = re.sub(r'^Note:\s*[^:]+ previously mentioned:\s*', '', reply, flags=re.IGNORECASE)
                reply = reply.strip()
            else:
                reply = f"({self.profile.name} has no response.)"

        except Exception as e:
            reply = f"({self.profile.name} experiences a moment of reflection... Error: {e})"

        # Add the generated reply to memory (without any prefixes)
        self.memory.add(session_id, self.profile.name, "assistant", reply)
        return reply

    def end_session(self, session_id: str):
        """Ends a chat session and cleans up resources."""
        self.memory.delete_session(session_id)
