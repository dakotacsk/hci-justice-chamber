import os
import uuid
import pygame
from agent import JusticeAgent
from config import AGENTS
from gui import ChatGUI


def main():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise SystemExit(
            "Set GOOGLE_API_KEY from https://aistudio.google.com/app/apikey"
        )

    agents = {k: JusticeAgent(k, GOOGLE_API_KEY) for k in AGENTS.keys()}
    agent_name_to_key = {v.name: k for k, v in AGENTS.items()}

    gui = ChatGUI(agents)

    def handle_send_message():
        user_input = gui.text
        if not user_input:
            return

        gui.text = ""

        active_agents = []
        for toggle in gui.toggle_switches:
            if toggle.is_on:
                agent_key = agent_name_to_key[toggle.label]
                active_agents.append(agents[agent_key])

        if not active_agents:
            gui.chat_history.append("No agents are active.")
            return

        # For simplicity, the user talks to the first active agent
        current_agent = active_agents[0]
        session_id = str(uuid.uuid4())
        reply = current_agent.send_message(session_id, user_input)
        gui.chat_history.append(f"{current_agent.profile.name}: {reply}")

        # Cross replies
        for agent in active_agents:
            if agent.profile.name != current_agent.profile.name:
                cross = agent.reply_to(session_id, current_agent.profile.name, reply)
                gui.chat_history.append(f"{agent.profile.name}: {cross}")

    def handle_toggle(toggle):
        if not toggle.is_on:
            agent_key = agent_name_to_key[toggle.label]
            agent = agents[agent_key]
            session_id = str(
                uuid.uuid4()
            )  # A dummy session id to delete all sessions for this agent
            agent.end_session(session_id)
            gui.action_history.append(f"{agent.profile.name} has left the council.")
        else:
            agent_key = agent_name_to_key[toggle.label]
            agent = agents[agent_key]
            gui.action_history.append(f"{agent.profile.name} has joined the council.")

    gui.handle_send_message = handle_send_message

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            for toggle in gui.toggle_switches:
                initial_state = toggle.is_on
                toggle.handle_event(event)
                if initial_state != toggle.is_on:
                    handle_toggle(toggle)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if gui.input_box.collidepoint(event.pos):
                    gui.active = not gui.active
                else:
                    gui.active = False

            if event.type == pygame.KEYDOWN and gui.active:
                if event.key == pygame.K_RETURN:
                    handle_send_message()
                elif event.key == pygame.K_BACKSPACE:
                    gui.text = gui.text[:-1]
                else:
                    gui.text += event.unicode

        gui.draw_background()
        gui.draw_dialogue_box()
        gui.draw_textbox()
        gui.draw_sprite()
        gui._draw_toggle_switches()
        gui._draw_action_history()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
