

import os
import sys
import uuid
import pygame
import csv
from agent import JusticeAgent
from config import AGENTS, AgentProfile
from gui import ChatGUI, CreationForm

CSV_FILE = "advocates.csv"

# --- ADVOCATE DATA HANDLING ---

def build_system_prompt(answers: dict) -> str:
    """Constructs a coherent system prompt from user answers."""
    return f"""
You are an advocate for the justice framework known as '{answers['name']}'.
Your Core Philosophy: {answers['definition']}
Your Core Values: Your guiding principles are {answers['values']}.
Your Personality: You are {answers['tone']}. You engage in dialogue with this personality, consistently reflecting your core philosophy and values in your reasoning and communication style.
Your Goal: To represent the '{answers['name']}' perspective clearly and persuasively in the Council of Justice.
""".strip()

def save_to_csv(data: dict):
    """Saves the custom advocate's data to a CSV file."""
    uid = str(uuid.uuid4())
    file_exists = os.path.isfile(CSV_FILE)
    
    row = {
        "uid": uid,
        "name": data['name'],
        "definition": data['definition'],
        "values": data['values'],
        "tone": data['tone'],
        "system_prompt": data['system_prompt']
    }

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
        
    print(f"✅ Saved your advocate under ID: {uid}\n")
    return uid

def load_latest_advocate() -> AgentProfile | None:
    """Loads the most recently created advocate from the CSV file."""
    if not os.path.isfile(CSV_FILE):
        return None
    
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        advocates = list(reader)
        if not advocates:
            return None
        
        latest_advocate_data = advocates[-1]
        print(f"✅ Loaded most recent advocate: {latest_advocate_data['name']}")
        return AgentProfile(
            name=latest_advocate_data['name'],
            system_prompt=latest_advocate_data['system_prompt']
        )

# --- MAIN APPLICATION ---

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_tokens", type=int, default=100, help="Maximum number of tokens for agent responses.")
    args = parser.parse_args()

    pygame.init()
    pygame.key.set_repeat(300, 30)
    
    SCREEN_WIDTH, SCREEN_HEIGHT = 1560, 878
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- Initial State Setup ---
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("""
        ERROR: API KEY NOT FOUND.
        Please set either the GOOGLE_API_KEY or OPENAI_API_KEY environment variable in your terminal.

        For example:
        export GOOGLE_API_KEY='YOUR_API_KEY'
        """)
        sys.exit(1)

    agents = {key: JusticeAgent(profile) for key, profile in AGENTS.items()}
    custom_advocate_profile = load_latest_advocate()
    if custom_advocate_profile:
        agents["custom"] = JusticeAgent(custom_advocate_profile)

    app_state = "CHAT"
    chat_gui = ChatGUI(agents, SCREEN_WIDTH, SCREEN_HEIGHT)
    creation_form = CreationForm(SCREEN_WIDTH, SCREEN_HEIGHT)

    # --- Main Loop ---
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if app_state == "CHAT":
            # --- CHAT STATE LOGIC ---
            for event in events:
                chat_gui.handle_event(event)
                if chat_gui.create_advocate_button.is_clicked(event):
                    app_state = "CREATION"
                    break
                if event.type == pygame.KEYDOWN and chat_gui.main_input_box.active:
                    if event.key == pygame.K_RETURN:
                        user_input = chat_gui.main_input_box.text
                        if not user_input: continue
                        
                        chat_gui.main_input_box.text = ""
                        chat_gui.chat_history.append(f"You: {user_input}")

                        active_agents = [agent for agent, toggle in zip(chat_gui.agents.values(), chat_gui.toggle_switches) if toggle.is_on]
                        if not active_agents:
                            chat_gui.chat_history.append("No agents are active.")
                            continue

                        session_id = str(uuid.uuid4())
                        for agent in active_agents:
                            agent.memory.add(session_id, "User", "user", user_input)

                        custom_agent = agents.get("custom")
                        if custom_agent and custom_agent in active_agents:
                            reply = custom_agent.generate_response(session_id, max_tokens=args.max_tokens)
                            chat_gui.chat_history.append(f"{custom_agent.profile.name}: {reply}")

                        for agent in active_agents:
                            if not custom_agent or agent.profile.name != custom_agent.profile.name:
                                cross_reply = agent.generate_response(session_id, max_tokens=args.max_tokens)
                                chat_gui.chat_history.append(f"{agent.profile.name}: {cross_reply}")
            
            chat_gui.draw(screen)

        elif app_state == "CREATION":
            # --- CREATION STATE LOGIC ---
            for event in events:
                new_advocate_data = creation_form.handle_event(event)
                if new_advocate_data:
                    # All fields must be filled
                    if all(new_advocate_data.values()):
                        system_prompt = build_system_prompt(new_advocate_data)
                        new_advocate_data['system_prompt'] = system_prompt
                        save_to_csv(new_advocate_data)
                        
                        # Create and add the new agent
                        new_profile = AgentProfile(name=new_advocate_data['name'], system_prompt=system_prompt)
                        agents["custom"] = JusticeAgent(new_profile)
                        
                        # Re-initialize the chat GUI with the new agent list
                        chat_gui = ChatGUI(agents, SCREEN_WIDTH, SCREEN_HEIGHT)
                        app_state = "CHAT"
                        break
            
            creation_form.draw(screen)

        pygame.display.flip()

    # --- Shutdown ---
    if agents:
        # Clear the database on exit
        any_agent = next(iter(agents.values()))
        any_agent.memory.clear_all()
        print(" DB cleared.")

    pygame.quit()

if __name__ == "__main__":
    main()
