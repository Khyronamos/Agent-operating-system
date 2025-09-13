import logging
import base64
import os
import asyncio
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger(__name__)

class WindowsControlManager:
    """
    Manager for Windows Control operations.

    This class provides a unified interface for Windows Control operations,
    using the Windows Control MCP server for automating Windows desktop actions.
    """

    def __init__(self, mcp_manager):
        """
        Initialize the Windows Control manager.

        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "windows-control"

    async def take_screenshot(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot of the desktop.

        Args:
            save_path: Path to save the screenshot (optional)

        Returns:
            Screenshot result with base64-encoded image data
        """
        logger.debug("Taking screenshot...")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "takeScreenshot",
            {}
        )

        # Save screenshot if path is provided
        if save_path and "imageData" in result:
            try:
                image_data = base64.b64decode(result["imageData"])
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(image_data)
                result["savedPath"] = save_path
            except Exception as e:
                logger.error(f"Error saving screenshot: {e}")

        return result

    async def mouse_click(self, x: int, y: int, button: str = "left") -> Dict[str, Any]:
        """
        Click the mouse at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button to click (left, right, middle)

        Returns:
            Click result
        """
        logger.debug(f"Clicking {button} mouse button at coordinates ({x}, {y})...")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "mouseClick",
            {
                "x": x,
                "y": y,
                "button": button
            }
        )

        return result

    async def mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        """
        Move the mouse to the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Move result
        """
        logger.debug(f"Moving mouse to coordinates ({x}, {y})...")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "mouseMove",
            {
                "x": x,
                "y": y
            }
        )

        return result

    async def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """
        Drag the mouse from start coordinates to end coordinates.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate

        Returns:
            Drag result
        """
        logger.debug(f"Dragging mouse from ({start_x}, {start_y}) to ({end_x}, {end_y})...")

        # Move to start position
        await self.mouse_move(start_x, start_y)

        # Perform drag
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "mouseDrag",
            {
                "x": end_x,
                "y": end_y
            }
        )

        return result

    async def type_text(self, text: str) -> Dict[str, Any]:
        """
        Type text.

        Args:
            text: Text to type

        Returns:
            Type result
        """
        logger.debug(f"Typing text: {text}")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "typeText",
            {
                "text": text
            }
        )

        return result

    async def press_keys(self, keys: List[str]) -> Dict[str, Any]:
        """
        Press a combination of keys.

        Args:
            keys: List of keys to press

        Returns:
            Key press result
        """
        logger.debug(f"Pressing keys: {keys}")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "pressKeys",
            {
                "keys": keys
            }
        )

        return result

    async def press_key_combo(self, combo: str) -> Dict[str, Any]:
        """
        Press a key combination (e.g., "ctrl+c").

        Args:
            combo: Key combination as a string (e.g., "ctrl+c")

        Returns:
            Key combo result
        """
        logger.debug(f"Pressing key combination: {combo}")

        # Split the combo into individual keys
        keys = combo.lower().split("+")

        return await self.press_keys(keys)

    async def get_screen_info(self) -> Dict[str, Any]:
        """
        Get information about the screen.

        Returns:
            Screen information
        """
        logger.debug("Getting screen information...")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "getScreenInfo",
            {}
        )

        return result

    async def find_image(self, image_path: str, confidence: float = 0.9) -> Dict[str, Any]:
        """
        Find an image on the screen.

        Args:
            image_path: Path to the image to find
            confidence: Confidence threshold (0.0 to 1.0)

        Returns:
            Image search result
        """
        logger.debug(f"Finding image {image_path} on screen...")

        # Read image file
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        result = await self.mcp_manager.call_tool(
            self.server_name,
            "findImage",
            {
                "imageData": image_data,
                "confidence": confidence
            }
        )

        return result

    async def click_image(self, image_path: str, confidence: float = 0.9) -> Dict[str, Any]:
        """
        Find an image on the screen and click it.

        Args:
            image_path: Path to the image to find and click
            confidence: Confidence threshold (0.0 to 1.0)

        Returns:
            Click result
        """
        logger.debug(f"Finding and clicking image {image_path} on screen...")

        # Find the image
        find_result = await self.find_image(image_path, confidence)

        if find_result.get("found"):
            # Click the center of the found image
            x = find_result.get("x") + find_result.get("width") // 2
            y = find_result.get("y") + find_result.get("height") // 2

            return await self.mouse_click(x, y)
        else:
            return {"success": False, "error": "Image not found"}

    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application.

        Args:
            app_name: Name of the application to open

        Returns:
            Open result
        """
        logger.debug(f"Opening application: {app_name}")

        # Press Win key
        await self.press_keys(["win"])

        # Wait a moment
        await asyncio.sleep(0.5)

        # Type the application name
        await self.type_text(app_name)

        # Wait a moment
        await asyncio.sleep(0.5)

        # Press Enter
        await self.press_keys(["enter"])

        return {"success": True, "app": app_name}

    async def close_application(self) -> Dict[str, Any]:
        """
        Close the active application.

        Returns:
            Close result
        """
        logger.debug("Closing active application...")

        # Press Alt+F4
        result = await self.press_key_combo("alt+f4")

        return result

    async def switch_application(self) -> Dict[str, Any]:
        """
        Switch to the next application.

        Returns:
            Switch result
        """
        logger.debug("Switching to next application...")

        # Press Alt+Tab
        result = await self.press_key_combo("alt+tab")

        return result

    async def automate_sequence(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Automate a sequence of actions.

        Args:
            actions: List of actions to perform

        Returns:
            Results of each action
        """
        logger.debug(f"Automating sequence of {len(actions)} actions...")

        results = []

        for action in actions:
            action_type = action.get("type")

            try:
                if action_type == "click":
                    result = await self.mouse_click(action.get("x"), action.get("y"), action.get("button", "left"))
                elif action_type == "move":
                    result = await self.mouse_move(action.get("x"), action.get("y"))
                elif action_type == "drag":
                    result = await self.mouse_drag(
                        action.get("start_x"), action.get("start_y"),
                        action.get("end_x"), action.get("end_y")
                    )
                elif action_type == "type":
                    result = await self.type_text(action.get("text"))
                elif action_type == "keys":
                    result = await self.press_keys(action.get("keys"))
                elif action_type == "combo":
                    result = await self.press_key_combo(action.get("combo"))
                elif action_type == "screenshot":
                    result = await self.take_screenshot(action.get("save_path"))
                elif action_type == "wait":
                    await asyncio.sleep(action.get("seconds", 1))
                    result = {"success": True, "action": "wait", "seconds": action.get("seconds", 1)}
                elif action_type == "find_image":
                    result = await self.find_image(action.get("image_path"), action.get("confidence", 0.9))
                elif action_type == "click_image":
                    result = await self.click_image(action.get("image_path"), action.get("confidence", 0.9))
                else:
                    result = {"success": False, "error": f"Unknown action type: {action_type}"}

                results.append(result)

                # If an action fails and stopOnError is true, stop the sequence
                if action.get("stopOnError", False) and not result.get("success", False):
                    break

            except Exception as e:
                logger.error(f"Error performing action {action_type}: {e}")
                results.append({"success": False, "error": str(e), "action": action_type})

                if action.get("stopOnError", False):
                    break

        return results
