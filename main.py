

import os
import sys
import uuid
import pygame
import csv
import random
import time
from agent import JusticeAgent
from config import AGENTS, AgentProfile
from gui import ChatGUI, CreationForm, AdvocateSelectionScreen

CSV_FILE = "advocates.csv"

# ADVOCATE DATA HANDLING

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

def load_all_custom_advocates() -> list[AgentProfile]:
    """Loads all custom advocates from the CSV file."""
    advocates = []
    if not os.path.isfile(CSV_FILE):
        return advocates
    
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            advocates.append(AgentProfile(
                name=row['name'],
                system_prompt=row['system_prompt']
            ))
    return advocates

# MAIN APPLICATION

import concurrent.futures

def main():

    pygame.init()
    pygame.key.set_repeat(300, 30)
    
    SCREEN_WIDTH, SCREEN_HEIGHT = 1248, 702
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
    all_custom_advocates = load_all_custom_advocates()
    
    # Add custom advocates to the agents dictionary, using their name as key
    for advocate_profile in all_custom_advocates:
        agents[advocate_profile.name] = JusticeAgent(advocate_profile)

    selected_advocate_key = None # To store the currently selected advocate
    chat_gui = ChatGUI(agents, SCREEN_WIDTH, SCREEN_HEIGHT, selected_advocate_key=selected_advocate_key, num_custom_advocates=len(all_custom_advocates))
    creation_form = CreationForm(SCREEN_WIDTH, SCREEN_HEIGHT)
    advocate_selection_screen = AdvocateSelectionScreen(SCREEN_WIDTH, SCREEN_HEIGHT, all_custom_advocates)

    app_state = "CHAT"

    # Main Loop
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if app_state == "CHAT":
            # CHAT STATE LOGIC
            for event in events:
                result = chat_gui.handle_event(event) # Capture the result
                if result == "select_advocate":
                    app_state = "ADVOCATE_SELECTION"
                    break
                if chat_gui.create_advocate_button.is_clicked(event):
                    app_state = "CREATION"
                    break
                if chat_gui.submit_button.is_clicked(event):
                    user_input = chat_gui.main_input_box.text
                    if not user_input: continue
                    
                    chat_gui.main_input_box.clear()
                    chat_gui.chat_history.append(f"You: {user_input}")
                    print(f"\nYou: {user_input}")

                    active_agents = [agent for agent, checkbox in zip(chat_gui.agents.values(), chat_gui.checkboxes) if checkbox.is_on]
                    if not active_agents:
                        chat_gui.chat_history.append("No agents are active.")
                        print("No agents are active.")
                        continue

                    session_id = str(uuid.uuid4())
                    for agent in active_agents:
                        agent.memory.add(session_id, "User", "user", user_input)

                    # Randomize the order of agents for responding
                    random.shuffle(active_agents)

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {executor.submit(agent.generate_response, session_id): agent for agent in active_agents}
                        for future in concurrent.futures.as_completed(futures):
                            agent = futures[future]
                            try:
                                reply = future.result()
                                chat_gui.chat_history.append(f"{agent.profile.name}: {reply}")
                                print(f"{agent.profile.name}: {reply}")
                            except Exception as exc:
                                print(f'{agent.profile.name} generated an exception: {exc}')
                    
                    chat_gui.current_chat_index = len(chat_gui.chat_history) - len(active_agents)
            
            chat_gui.draw(screen)

        elif app_state == "CREATION":
            # CREATION STATE LOGIC
            for event in events:
                result = creation_form.handle_event(event)
                if result:
                    if result == "back":
                        app_state = "CHAT"
                        break
                    
                    # All fields must be filled
                    if isinstance(result, dict) and all(result.values()):
                        system_prompt = build_system_prompt(result)
                        result['system_prompt'] = system_prompt
                        save_to_csv(result)
                        
                        # Create and add the new agent
                        new_profile = AgentProfile(name=result['name'], system_prompt=system_prompt)
                        agents["custom"] = JusticeAgent(new_profile)
                        
                        # Re-initialize the chat GUI with the new agent list
                        chat_gui = ChatGUI(agents, SCREEN_WIDTH, SCREEN_HEIGHT, selected_advocate_key=selected_advocate_key, num_custom_advocates=len(all_custom_advocates))
                        app_state = "CHAT"
                        break
            
            creation_form.draw(screen)

        elif app_state == "ADVOCATE_SELECTION":
            for event in events:
                result = advocate_selection_screen.handle_event(event)
                if result == "back":
                    app_state = "CHAT"
                    break
                elif result: # An advocate key was returned
                    selected_advocate_key = result
                    print(f"Selected advocate: {selected_advocate_key}")
                    # Re-initialize chat_gui with the newly selected advocate
                    chat_gui = ChatGUI(agents, SCREEN_WIDTH, SCREEN_HEIGHT, selected_advocate_key=selected_advocate_key, num_custom_advocates=len(all_custom_advocates))
                    app_state = "CHAT"
                    break
            advocate_selection_screen.draw(screen)

        pygame.display.flip()

    # Shutdown
    if agents:
        # Clear the database on exit
        any_agent = next(iter(agents.values()))
        any_agent.memory.clear_all()
        print(" DB cleared.")

    pygame.quit()

if __name__ == "__main__":
    main()
