# Project: JARVIS - Just A Rather Very Intelligent System

## Project Overview

This project is a Python-based AI assistant named JARVIS. It is designed to run locally, leveraging the Ollama framework for large language model inference. The system is specifically optimized for machines with an NVIDIA RTX 3050 GPU, with a focus on managing VRAM and selecting appropriate models based on the task and system load.

The assistant is built with a modular architecture, consisting of a core engine, a dynamic skill loader, and various manager modules for configuration, memory, and system control.

**Core Technologies:**

*   **Language:** Python
*   **LLM Framework:** Ollama
*   **Key Libraries:** `pyttsx3` (text-to-speech), `faster-whisper` (speech-to-text), `psutil` (system monitoring), `asyncio` (asynchronous operations).

**Architecture:**

*   **`jarvis.py`**: The main entry point for the application. It handles command-line arguments and provides an interactive menu for the user.
*   **`jarvis_core_optimized.py`**: The central component of the assistant, responsible for processing user queries, managing context, and interacting with the Ollama models.
*   **`jarvis_skills.py` & `skills/` directory**: Implements a skill-based system. New functionalities can be added by creating new skill modules in the `skills` directory. Each skill can define keywords to respond to specific user requests.
*   **`jarvis_config.json`**: A configuration file that allows users to customize settings for voice, models, and application behavior.
*   **`model_router.py`**: A crucial component for performance optimization. It dynamically selects the most appropriate LLM based on the user's query and the current VRAM usage.
*   **`main.py`**: Appears to be a monolithic, all-in-one version of the assistant, likely from an earlier stage of development. The more recent, modular structure is preferred for development.

## Building and Running

### 1. Prerequisites

*   **Ollama:** Install Ollama from [https://ollama.com](https://ollama.com).
*   **Python:** Python 3.9 or higher is recommended.

### 2. Installation

1.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Download LLM Models:**
    The system is optimized for the following models. Pull them using the `ollama` command:
    ```bash
    ollama pull gemma:2b
    ollama pull phi3:3.8b
    ollama pull deepseek-coder:6.7b
    ```

3.  **Run the JARVIS Installer:**
    This will set up the necessary configurations and databases.
    ```bash
    python jarvis.py install
    ```

### 3. Running the Assistant

*   **Interactive Chat Mode:**
    ```bash
    python jarvis.py chat
    ```

*   **Interactive Menu:**
    To see all available options.
    ```bash
    python jarvis.py
    ```

*   **Quick Query:**
    For a single, direct question.
    ```bash
    python jarvis.py "What is the weather like today?"
    ```

*   **Run a Feature Demo:**
    ```bash
    python jarvis.py demo
    ```

## Development Conventions

*   **Modularity:** The project is structured into distinct modules, each with a specific responsibility (e.g., `jarvis_config.py`, `jarvis_skills.py`). This pattern should be followed when adding new features.
*   **Skill-Based Architecture:** To add new capabilities, create a new Python file in the `skills/` directory. The file should contain a class that inherits from `BaseSkill` (defined in `jarvis_skills.py`). This class should implement a `handle` method and define a list of `keywords` that trigger the skill.
*   **Asynchronous Code:** The core of the application uses `asyncio` for non-blocking operations, especially when interacting with the Ollama models. New code should be written in an async-first manner where appropriate.
*   **Configuration:** Application settings are managed through `jarvis_config.json`. Avoid hardcoding values; instead, add them to the configuration file and access them through the `ConfigManager`.
*   **Code Style:** The code generally follows PEP 8 standards, uses f-strings for string formatting, and includes type hints.
