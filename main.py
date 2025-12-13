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
from audio import SpeechRecognizer
from speech2text import Speech2Text

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
        "name": data["name"],
        "definition": data["definition"],
        "values": data["values"],
        "tone": data["tone"],
        "system_prompt": data["system_prompt"],
    }

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
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

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        advocates = list(reader)
        if not advocates:
            return None

        latest_advocate_data = advocates[-1]
        print(f"✅ Loaded most recent advocate: {latest_advocate_data['name']}")
        return AgentProfile(
            name=latest_advocate_data["name"],
            system_prompt=latest_advocate_data["system_prompt"],
        )


def load_all_custom_advocates() -> list[AgentProfile]:
    """Loads all custom advocates from the CSV file."""
    advocates = []
    if not os.path.isfile(CSV_FILE):
        return advocates

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            advocates.append(
                AgentProfile(name=row["name"], system_prompt=row["system_prompt"])
            )
    return advocates


def delete_custom_advocate(advocate_name: str) -> bool:
    """Deletes a custom advocate from the CSV file by name."""
    if not os.path.isfile(CSV_FILE):
        return False

    # Read all advocates
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter out the one to delete
    original_count = len(rows)
    rows = [row for row in rows if row["name"] != advocate_name]

    if len(rows) == original_count:
        return False  # Advocate not found

    # Write back the remaining advocates
    if rows:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    else:
        # If no rows left, delete the file
        os.remove(CSV_FILE)

    print(f"✅ Deleted advocate: {advocate_name}\n")
    return True


# MAIN APPLICATION

import concurrent.futures


def main():

    pygame.init()
    pygame.key.set_repeat(300, 30)

    # Initialize speech recognizer
    speech = SpeechRecognizer()
    speech.start()

    speech2text = Speech2Text()

    SCREEN_WIDTH, SCREEN_HEIGHT = 1728, 972
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- Initial State Setup ---
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print(
            """
        ERROR: API KEY NOT FOUND.
        Please set either the GOOGLE_API_KEY or OPENAI_API_KEY environment variable in your terminal.

        For example:
        export GOOGLE_API_KEY='YOUR_API_KEY'
        """
        )
        sys.exit(1)

    agents = {key: JusticeAgent(profile) for key, profile in AGENTS.items()}
    all_custom_advocates = load_all_custom_advocates()

    # Store default agents separately
    default_agents = agents.copy()

    selected_advocate_key = (
        None  # To store the currently selected custom advocate (only one at a time)
    )

    # Function to rebuild agents dict with selected custom advocate
    def rebuild_agents():
        new_agents = default_agents.copy()
        if selected_advocate_key:
            # Find and add the selected custom advocate
            for advocate_profile in all_custom_advocates:
                if advocate_profile.name == selected_advocate_key:
                    new_agents[advocate_profile.name] = JusticeAgent(advocate_profile)
                    break
        return new_agents

    # Initial agents setup
    agents = rebuild_agents()
    chat_gui = ChatGUI(
        agents,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        selected_advocate_key=selected_advocate_key,
        num_custom_advocates=len(all_custom_advocates),
        speech_recognizer=speech,
    )
    creation_form = CreationForm(SCREEN_WIDTH, SCREEN_HEIGHT, speech_recognizer=speech)
    advocate_selection_screen = AdvocateSelectionScreen(
        SCREEN_WIDTH, SCREEN_HEIGHT, all_custom_advocates, default_agents
    )

    # Use a single session_id for the entire application session
    session_id = str(uuid.uuid4())
    print(f"Session started with ID: {session_id}")

    app_state = "CHAT"

    # Main Loop
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # Only process voice input if space bar is pressed
        keys = pygame.key.get_pressed()
        
        # Handle voice input based on current app state
        if app_state == "CHAT":
            elapsed_time = time.time() - chat_gui.get_voice_detected()
            speech.listening_enabled = keys[pygame.K_SPACE] or elapsed_time < 2
            chat_gui.voice_mode_active = keys[pygame.K_SPACE]
            if keys[pygame.K_SPACE] or elapsed_time < 2:
                # Wait 2 seconds to process detected voice
                new_speech = speech.get_latest_text()
                if new_speech:
                    speech.listening_enabled = False
                    print(f"Voice command: {new_speech}")

                    chat_gui.set_caption(f"You: {new_speech}")
                    chat_gui.draw(screen)
                    pygame.display.update()

                    time.sleep(1.5)

                    chat_gui.chat_history.append(f"You: {new_speech}")
                    print(f"\nYou: {new_speech}")

                    active_agents = [
                        agent
                        for agent, checkbox in zip(
                            chat_gui.agents.values(), chat_gui.checkboxes
                        )
                        if checkbox.is_on
                    ]
                    if not active_agents:
                        chat_gui.chat_history.append("No agents are active.")
                        print("No agents are active.")
                        continue

                    # Use the same session_id for the entire session
                    for agent in active_agents:
                        agent.memory.add(session_id, "User", "user", new_speech)

                    # Randomize the order of agents for responding
                    random.shuffle(active_agents)

                    # Process agents with rate limiting to avoid 429 errors
                    # Process in smaller batches with delays between batches
                    batch_size = 2  # Process 2 agents at a time
                    for i in range(0, len(active_agents), batch_size):
                        batch = active_agents[i : i + batch_size]
                        with concurrent.futures.ThreadPoolExecutor(
                            max_workers=batch_size
                        ) as executor:
                            # Mark agents as thinking when submitting
                            for agent in batch:
                                chat_gui.set_agent_thinking(agent.profile.name, True)

                            futures = {
                                executor.submit(agent.generate_response, session_id): agent
                                for agent in batch
                            }
                            count = 0
                            for future in concurrent.futures.as_completed(futures):
                                agent = futures[future]
                                try:
                                    reply = future.result()
                                    chat_gui.chat_history.append(
                                        f"{agent.profile.name}: {reply}"
                                    )
                                    print(f"{agent.profile.name}: {reply}")
                                    chat_gui.current_speaker = agent.profile.name
                                    chat_gui.set_caption(f"{agent.profile.name}: {reply}")
                                    chat_gui.draw(screen)
                                    pygame.display.update()
                                    speech2text.speak(reply, agent.profile.name)
                                    chat_gui.current_speaker = ""
                                except Exception as exc:
                                    print(
                                        f"{agent.profile.name} generated an exception: {exc}"
                                    )
                                finally:
                                    # Mark agent as done thinking
                                    chat_gui.set_agent_thinking(agent.profile.name, False)
                                count = count + 1

                        # Add a small delay between batches to avoid rate limiting
                        if i + batch_size < len(active_agents):
                            time.sleep(0.5)  # 500ms delay between batches
        elif app_state == "CREATION":
            # Only enable voice recognition when SPACE is actively held
            # This prevents background noise from being captured
            elapsed_time = time.time() - creation_form.get_voice_detected()
            creation_form.voice_mode_active = keys[pygame.K_SPACE]
            
            # Only listen when SPACE is held (not after release)
            if keys[pygame.K_SPACE]:
                speech.listening_enabled = True
                # Process voice input for creation form
                new_speech = speech.get_latest_text()
                if new_speech:
                    # Only process if we got meaningful text (more than a few characters)
                    if len(new_speech.strip()) > 3:
                        speech.listening_enabled = False
                        print(f"Voice input for creation form: {new_speech}")
                        creation_form.handle_voice_input(new_speech)
            else:
                # Disable listening when SPACE is not held
                speech.listening_enabled = False

        if app_state == "CHAT":
            # CHAT STATE LOGIC
            for event in events:
                result = chat_gui.handle_event(event)  # Capture the result
                if result == "select_advocate":
                    app_state = "ADVOCATE_SELECTION"
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        app_state = "CREATION"
                        break
            chat_gui.draw(screen)

        elif app_state == "CREATION":
            # CREATION STATE LOGIC
            for event in events:
                # Handle LEFT arrow key to exit creation mode (H3: User control and freedom)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        app_state = "CHAT"
                        # Reset creation form to first question
                        creation_form.current_question_index = 0
                        creation_form.active_input_index = 0
                        break
                
                result = creation_form.handle_event(event)
                if result:
                    if result == "back":
                        app_state = "CHAT"
                        # Reset creation form to first question
                        creation_form.current_question_index = 0
                        creation_form.active_input_index = 0
                        break

                    # All fields must be filled
                    if isinstance(result, dict) and all(result.values()):
                        system_prompt = build_system_prompt(result)
                        result["system_prompt"] = system_prompt
                        save_to_csv(result)

                        # Reload custom advocates to include the new one
                        all_custom_advocates = load_all_custom_advocates()

                        # Automatically select the newly created advocate
                        selected_advocate_key = result["name"]

                        # Rebuild agents and recreate screens
                        agents = rebuild_agents()
                        advocate_selection_screen = AdvocateSelectionScreen(
                            SCREEN_WIDTH,
                            SCREEN_HEIGHT,
                            all_custom_advocates,
                            default_agents,
                        )
                        chat_gui = ChatGUI(
                            agents,
                            SCREEN_WIDTH,
                            SCREEN_HEIGHT,
                            selected_advocate_key=selected_advocate_key,
                            num_custom_advocates=len(all_custom_advocates),
                            speech_recognizer=speech,
                        )
                        # Recreate creation form with speech recognizer
                        creation_form = CreationForm(SCREEN_WIDTH, SCREEN_HEIGHT, speech_recognizer=speech)
                        app_state = "CHAT"
                        break

            creation_form.draw(screen)

        elif app_state == "ADVOCATE_SELECTION":
            for event in events:
                # Handle LEFT arrow key to exit selection mode (H3: User control and freedom)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        app_state = "CHAT"
                        break
                
                result = advocate_selection_screen.handle_event(event)
                if result == "back":
                    app_state = "CHAT"
                    break
                elif isinstance(result, tuple) and result[0] == "delete":
                    # Handle deletion
                    advocate_name = result[1]
                    if delete_custom_advocate(advocate_name):
                        # Reload custom advocates
                        all_custom_advocates = load_all_custom_advocates()
                        # If deleted advocate was selected, clear selection
                        if selected_advocate_key == advocate_name:
                            selected_advocate_key = None
                        # Rebuild agents and recreate screens
                        agents = rebuild_agents()
                        advocate_selection_screen = AdvocateSelectionScreen(
                            SCREEN_WIDTH,
                            SCREEN_HEIGHT,
                            all_custom_advocates,
                            default_agents,
                        )
                        chat_gui = ChatGUI(
                            agents,
                            SCREEN_WIDTH,
                            SCREEN_HEIGHT,
                            selected_advocate_key=selected_advocate_key,
                            num_custom_advocates=len(all_custom_advocates),
                            speech_recognizer=speech,
                        )
                elif result:  # An advocate key was returned (only custom advocates now)
                    advocate_name = result
                    # All results from selection screen are custom advocates
                    selected_advocate_key = advocate_name
                    print(f"Selected custom advocate: {selected_advocate_key}")
                    # Rebuild agents and recreate chat_gui
                    agents = rebuild_agents()
                    chat_gui = ChatGUI(
                        agents,
                        SCREEN_WIDTH,
                        SCREEN_HEIGHT,
                        selected_advocate_key=selected_advocate_key,
                        num_custom_advocates=len(all_custom_advocates),
                    )
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

    speech.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
