import os

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_file_path = os.path.join(current_dir, "prompts.md")

# Read the system prompt from the Markdown file
try:
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    # Fallback or error handling if file is missing (though it should be there)
    SYSTEM_PROMPT = "Error: prompts.md not found."
