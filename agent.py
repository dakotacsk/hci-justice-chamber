# justice_agents/agent.py
import google.generativeai as genai
from config import AGENTS, MODEL_NAME
from memory import ChatMemory

class JusticeAgent:
    def __init__(self, agent_key: str, api_key: str, db_path="./justice_memory.db"):
        if agent_key not in AGENTS:
            raise ValueError(f"Unknown agent: {agent_key}")
        self.profile = AGENTS[agent_key]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.memory = ChatMemory(db_path)

    def _build_context(self, session_id: str) -> str:
        history = self.memory.get_recent(session_id)
        context = ""
        for m in history[-12:]:
            prefix = f"[{m['agent']} - {m['role']}]: "
            context += prefix + m["content"].strip() + "\n"
        return context.strip()

    def send_message(self, session_id: str, text: str) -> str:
        self.memory.add(session_id, self.profile.name, "user", text)
        context = self._build_context(session_id)
        prompt = f"{self.profile.system_prompt}\n\nContext:\n{context}\n\nUser: {text}\n{self.profile.name}:"
        response = self.model.generate_content(prompt, safety_settings={
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
        })
        reply = response.text.strip()
        self.memory.add(session_id, self.profile.name, "assistant", reply)
        return reply

    def reply_to(self, session_id: str, other_agent_name: str, text: str) -> str:
        context = self._build_context(session_id)
        prompt = (
            f"{self.profile.system_prompt}\n\n"
            f"Context (recent dialogue among agents):\n{context}\n\n"
            f"{other_agent_name}: {text}\n{self.profile.name}:"
        )
        response = self.model.generate_content(prompt, safety_settings={
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
        })
        reply = response.text.strip()
        self.memory.add(session_id, self.profile.name, "assistant", reply)
        return reply

    def end_session(self, session_id: str):
        self.memory.delete_session(session_id)