# skills/computer_vision_skill.py
"""
Computer Vision Skill for JARVIS
"""

import asyncio
import logging
import json
from typing import Any, Optional

import pyautogui
import mss
from PIL import Image
import google.generativeai as genai

from jarvis_skills import BaseSkill

logger = logging.getLogger("Jarvis.Skills.ComputerVision")

class Skill(BaseSkill):
    """
    A skill that allows JARVIS to see and interact with the screen.
    """
    name: str = "computer_vision"
    keywords: list[str] = ["click on", "type in", "press"]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """
        Handles computer vision commands.
        
        Example:
        "JARVIS, click on the 'Submit' button."
        "JARVIS, type 'hello world' in the search bar."
        "JARVIS, press the 'Enter' key."
        """
        logger.info("Computer Vision Skill handling: %s", text)
        text_lower = text.lower()

        # 1. Determine action and target
        action = None
        target = None
        value_to_type = None

        if "click on" in text_lower:
            action = "click"
            target = text_lower.split("click on")[-1].strip()
        elif "type in" in text_lower:
            action = "type"
            parts = text.split("type")[-1].strip().split("in")
            if len(parts) == 2:
                value_to_type = parts[0].strip().strip("'\"")
                target = parts[1].strip()
            else:
                return "Invalid 'type in' command. Use 'type \"text\" in target_element'."
        elif "press" in text_lower:
            action = "press"
            target = text_lower.split("press")[-1].strip()
            # For 'press', the target is the key itself. No need for vision.
            try:
                pyautogui.press(target)
                return f"Pressed the '{target}' key."
            except Exception as e:
                return f"Failed to press key '{target}': {e}"
        
        if not action or not target:
            return "I didn't understand the computer vision command."

        # 2. Get Gemini API Key
        api_key = jarvis.config.get("GEMINI_API_KEY")
        if not api_key:
            return "Gemini API key is not configured in jarvis_config.json."

        # 3. Capture the screen
        screenshot_path = "temp_screenshot.png"
        with mss.mss() as sct:
            sct.shot(output=screenshot_path)
        logger.info(f"Screenshot captured and saved to {screenshot_path}")

        # 4. Prepare the prompt for Gemini
        prompt = f"""
        You are an expert in UI analysis. Your task is to find the coordinates of a specific UI element on the screen.
        The user wants to '{action}' on/in: '{target}'.
        Analyze the provided screenshot and return the coordinates of the center of this element.
        Your response must be a JSON object with the following format: {{"x": <x_coordinate>, "y": <y_coordinate>}}
        If you cannot find the element, return {{"error": "Element not found"}}
        """

        try:
            # 5. Configure Gemini and send the request
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro-vision')
            img = Image.open(screenshot_path)
            
            response = await model.generate_content_async([prompt, img])

            # 6. Parse the response and perform the action
            if response.text:
                logger.info(f"Gemini response: {response.text}")
                try:
                    json_response = response.text.strip().replace("```json", "").replace("```", "")
                    coords = json.loads(json_response)
                    
                    if "error" in coords:
                        return f"I could not find the element '{target}' on the screen."
                    
                    x, y = coords.get("x"), coords.get("y")
                    if x is not None and y is not None:
                        if action == "click":
                            pyautogui.click(x, y)
                            return f"Clicked on '{target}' at coordinates ({x}, {y})."
                        elif action == "type":
                            pyautogui.click(x, y) # Focus the element first
                            await asyncio.sleep(0.2)
                            pyautogui.write(value_to_type, interval=0.05)
                            return f"Typed '{value_to_type}' in '{target}'."
                    else:
                        return "I found the element, but the coordinates were invalid."

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from Gemini response: {response.text}")
                    return "I received an invalid response from the AI. I couldn't perform the action."
            else:
                return "I received an empty response from the AI. I couldn't perform the action."

        except Exception as e:
            logger.error(f"An error occurred while using the Gemini API: {e}")
            return "An error occurred while trying to analyze the screen."

