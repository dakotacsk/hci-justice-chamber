# HCI Justice Chamber

## Project Description

This project simulates a "Justice Chamber" where a user can interact with five different AI agents, each embodying a distinct philosophical approach to justice: Utilitarian, Restorative, Meritocratic, and Rawlsian. The application provides a graphical user interface (GUI) for real-time interaction, allowing users to explore how different ethical frameworks might approach complex scenarios.

## Features

*   **Five Justice Agents**: Interact with AI agents representing Utilitarian, Restorative, Meritocratic, and Rawlsian perspectives.
*   **Interactive GUI**: A user-friendly interface built with `tkinter` for seamless conversation.
*   **Concurrent Agent Responses**: Agents respond in parallel using threading, ensuring a smooth and responsive experience.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.x**: Download from [python.org](https://www.python.org/downloads/)
*   **pip**: Python's package installer (usually comes with Python).

## Installation

1.  **Clone the repository** (if you haven't already):

    ```bash
    git clone <repository_url>
    cd hci-justice-chamber
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

## API Key Setup

This project uses the Google Gemini API. You need to set your `GOOGLE_API_KEY` as an environment variable.

1.  **Obtain a Google Gemini API Key**: Follow the instructions on the [Google AI Studio](https://aistudio.google.com/app/apikey) website.

2.  **Set the environment variable**:

    **On macOS/Linux:**

    ```bash
    export GOOGLE_API_KEY="YOUR_API_KEY"
    ```

    **On Windows (Command Prompt):**

    ```bash
    set GOOGLE_API_KEY="YOUR_API_KEY"
    ```

    **On Windows (PowerShell):**

    ```powershell
    $env:GOOGLE_API_KEY="YOUR_API_KEY"
    ```

    Replace `"YOUR_API_KEY"` with your actual Gemini API key.

## How to Run

Once the dependencies are installed and your API key is set, you can run the application:

```bash
python main.py
```

## Usage

1.  The GUI window will appear.
2.  Type your message into the input field at the bottom.
3.  Press `Enter` or click the "Send" button.
4.  Each of the five justice agents will process your input and display their responses in the chat area.

Enjoy exploring the different perspectives on justice!