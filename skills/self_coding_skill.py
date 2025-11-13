import logging
import re
import os
import ast
from jarvis_skills import BaseSkill
from typing import Any, Optional

logger = logging.getLogger("Jarvis.SelfCodingSkill")

class SelfCodingSkill(BaseSkill):
    name = "self_coding"
    keywords = [
        "modify your code", 
        "edit your code", 
        "change file", 
        "edit file", 
        "modify file"
    ]

    # Core files that should not be modified to prevent system instability.
    CORE_FILES_BLACKLIST = [
        "jarvis_core_optimized.py",
        "jarvis_turbo_manager.py",
        "jarvis_config.py",
        "self_coding_skill.py" # The skill should not edit itself.
    ]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """
        Handles requests for self-modification of the assistant's codebase.
        """
        # Regex to parse "edit file 'path/to/file.py' to 'do this change'"
        match = re.search(r"(?:edit|change|modify) file ['"](.+?)['"] to ['"](.+?)['"]", text, re.IGNORECASE)
        
        if not match:
            return "I didn't understand that request. Please use the format: \"edit file 'path/to/your/file.py' to 'your detailed change request'\".."

        file_path_relative = match.group(1)
        modification_request = match.group(2)
        
        # Prevent traversal attacks and check blacklist
        if ".." in file_path_relative or os.path.basename(file_path_relative) in self.CORE_FILES_BLACKLIST:
            logger.warning(f"Attempted to modify a blacklisted or invalid file: {file_path_relative}")
            return f"For safety reasons, I cannot modify the core file: {os.path.basename(file_path_relative)}."

        # Construct absolute path
        # Assumes the script is run from the project root.
        project_root = os.getcwd()
        file_path_absolute = os.path.join(project_root, file_path_relative)

        if not os.path.exists(file_path_absolute):
            return f"I could not find the file: {file_path_relative}"

        try:
            with open(file_path_absolute, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path_absolute}: {e}")
            return f"I encountered an error reading the file: {e}"

        # Construct the prompt for the Gemini model
        prompt = f"""You are an expert Python programmer AI. Your task is to modify the following Python file based on a user's request.
You MUST only output the complete, modified Python code for the file.
Do not include any explanations, comments, or markdown code fences like ```python ... ```.
Just provide the raw, full code for the modified file.

User Request: '{modification_request}'

Original File Content:
---
{original_content}
---

Modified File Content:
"""
        
        logger.info(f"Requesting code modification from Gemini for file: {file_path_relative}")
        
        full_response = ""
        try:
            # Use the Gemini query method, collecting the streamed response.
            async for chunk in jarvis.turbo.query_gemini(prompt=prompt, stream=True):
                content = chunk.get('message', {}).get('content', '')
                if content:
                    full_response += content
        except Exception as e:
            logger.error(f"Error querying Gemini for self-coding: {e}")
            return f"I encountered an error with the AI model while processing the change: {e}"

        if not full_response:
            return "The AI model did not return a modification. I will not proceed."

        # Validate the generated Python code
        try:
            ast.parse(full_response)
            logger.info("Generated code is valid Python syntax.")
        except SyntaxError as e:
            logger.error(f"Generated code is invalid: {e}")
            return f"The AI generated invalid Python code, so I am aborting the change. Error: {e}"

        # Write to a .new file for safety
        new_file_path = file_path_absolute + ".new"
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(full_response)
            logger.info(f"Successfully wrote modified code to {new_file_path}")
        except Exception as e:
            logger.error(f"Error writing to new file {new_file_path}: {e}")
            return f"I failed to write the new file. Error: {e}"

        return f"I have created a new version of '{os.path.basename(file_path_relative)}' with the requested changes. It has been saved to '{os.path.basename(new_file_path)}' for your review. Please check it and, if it's correct, rename it to apply the changes."