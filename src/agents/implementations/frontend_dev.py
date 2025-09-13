# agents/implementations/frontend_dev.py
import asyncio
import logging
import random
from typing import Dict, Any, List

from agents.specialized import APIA_SpecializedAgent
from utils.protocols import A2ATaskContext, A2ATaskResult
from utils.models import A2AArtifact, A2ATextPart, A2ADataPart, A2AMessage

logger = logging.getLogger(__name__)

class APIA_FrontendDeveloperAgent(APIA_SpecializedAgent):
    """
    Frontend Developer Agent for creating UI components, layouts, and client-side logic.

    Specializes in tasks like:
    - Generating HTML, CSS, and JavaScript/TypeScript for UI elements.
    - Implementing page layouts and responsive design.
    - Integrating with backend APIs.
    - Basic client-side validation and interactivity.
    """

    async def _initialize_domain_resources(self):
        """Initialize frontend development resources."""
        self._supported_frameworks = ["react", "vue", "angular", "html_css_js"]
        self._component_templates: Dict[str, Dict[str, str]] = {
            "react": {
                "button": "const {label}Button = ({ onClick }) => <button onClick={onClick}>{label}</button>;",
                "input": "const {label}Input = ({ value, onChange }) => <label>{label}: <input value={value} onChange={onChange} /></label>;",
                "form": """
const {formName}Form = ({ onSubmit }) => {
  // Add form state and fields here
  return (
    <form onSubmit={onSubmit}>
      {/* Add form elements, e.g., using Input components */}
      <button type="submit">Submit</button>
    </form>
  );
};
"""
            },
            "html_css_js": {
                "button": '<button id="{id}">{label}</button>\n<style>#{id} { /* CSS */ }</style>\n<script>document.getElementById("{id}").onclick = () => {{ /* JS */ }};</script>',
                "input": '<label for="{id}">{label}:</label><input type="text" id="{id}" name="{id}">',
                "form": """
<form id="{formName}Form">
  <!-- Form fields here -->
  <button type="submit">Submit</button>
</form>
<script>
  document.getElementById("{formName}Form").addEventListener('submit', function(event) {
    event.preventDefault();
    // Handle form submission
  });
</script>
"""
            }
            # Add Vue/Angular templates as needed
        }
        logger.info(f"FrontendDeveloperAgent ({self.id}) initialized domain resources.")

    async def _register_skills(self):
        """Register frontend development skills."""
        # This populates the local _skill_registry for use in _handle_domain_task
        self._skill_registry.update({
            "create_ui_component": {
                "name": "Create UI Component",
                "description": "Generate code for a specific UI component (e.g., button, form, card).",
                "examples": [
                    "Create a React login form component",
                    "Generate HTML/CSS for a product card"
                ]
            },
            "implement_page_layout": {
                "name": "Implement Page Layout",
                "description": "Generate HTML/CSS structure for a page layout (e.g., header, footer, sidebar).",
                "examples": [
                    "Design a two-column layout with a fixed sidebar",
                    "Create a responsive navigation bar"
                ]
            },
            "integrate_frontend_api": {
                "name": "Integrate Frontend with API",
                "description": "Write client-side code to fetch data from or send data to a backend API.",
                "examples": [
                    "Fetch user data from /api/users and display it",
                    "Submit form data to /api/submit"
                ]
            }
        })
        logger.info(f"FrontendDeveloperAgent ({self.id}) registered skills: {list(self._skill_registry.keys())}")


    async def _handle_domain_task(self, context: A2ATaskContext, skill_id: str, subtask_description: str) -> A2ATaskResult:
        """
        Handle frontend development tasks by routing to specific handlers.
        """
        await context.update_status("working", message_text=f"FrontendDev working on: {subtask_description}")

        if skill_id == "create_ui_component":
            return await self._handle_create_ui_component(context, subtask_description)
        elif skill_id == "implement_page_layout":
            return await self._handle_implement_page_layout(context, subtask_description)
        elif skill_id == "integrate_frontend_api":
            return await self._handle_integrate_frontend_api(context, subtask_description)
        else:
            logger.warning(f"FrontendDeveloperAgent ({self.id}) received unknown skill_id for domain task: {skill_id}")
            return A2ATaskResult(
                status="failed",
                message=A2AMessage(role="agent", parts=[A2ATextPart(text=f"Unknown frontend skill: {skill_id}")])
            )

    def _determine_framework(self, context: A2ATaskContext, description: str) -> str:
        """Determine the frontend framework to use."""
        # Check context metadata first
        if context.task.metadata and context.task.metadata.get("framework"):
            fw = context.task.metadata["framework"].lower()
            if fw in self._supported_frameworks:
                return fw

        # Check description
        description_lower = description.lower()
        for fw_name in self._supported_frameworks:
            if fw_name in description_lower:
                return fw_name
        return "html_css_js" # Default

    async def _handle_create_ui_component(self, context: A2ATaskContext, description: str) -> A2ATaskResult:
        framework = self._determine_framework(context, description)
        
        # Basic parsing for component type and name (can be much more sophisticated)
        component_type = "button" # Default
        component_name = "myComponent"
        description_lower = description.lower()

        if "form" in description_lower: component_type = "form"
        elif "input" in description_lower: component_type = "input"
        elif "button" in description_lower: component_type = "button"

        # Try to extract a name like "login form" -> "login"
        parts = description_lower.split()
        if "component" in parts: parts.remove("component")
        if component_type in parts: parts.remove(component_type)
        # A very naive way to get a name
        potential_name = "_".join(p for p in parts if p not in ["create", "a", "an", "the", "for"])
        if potential_name: component_name = potential_name

        code_template = self._component_templates.get(framework, {}).get(component_type)
        generated_code = f"// Placeholder for {framework} {component_type}: {component_name}\n"
        if code_template:
            # Basic templating
            generated_code = code_template.format(label=component_name.capitalize(), id=component_name, formName=component_name)
        else:
            generated_code += f"// No specific template found for {framework} {component_type}. Please implement manually."

        await asyncio.sleep(random.uniform(0.5, 1.5)) # Simulate generation time

        return A2ATaskResult(
            status="completed",
            artifacts=[
                A2AArtifact(
                    name=f"{component_name}_{component_type}.{framework.split('_')[0]}", # e.g. login_form.react or myButton.html
                    description=f"Generated {framework} code for {component_type} '{component_name}'",
                    parts=[A2ATextPart(text=generated_code)]
                )
            ]
        )

    async def _handle_implement_page_layout(self, context: A2ATaskContext, description: str) -> A2ATaskResult:
        framework = self._determine_framework(context, description)
        # Placeholder logic
        layout_description = description
        html_code = f"<!-- HTML for {layout_description} using {framework} -->\n<div>Page Content Here</div>"
        css_code = f"/* CSS for {layout_description} */\nbody {{ margin: 0; font-family: sans-serif; }}"
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        return A2ATaskResult(
            status="completed",
            artifacts=[
                A2AArtifact(name="layout.html", description="Page Layout HTML", parts=[A2ATextPart(text=html_code)]),
                A2AArtifact(name="layout.css", description="Page Layout CSS", parts=[A2ATextPart(text=css_code)])
            ]
        )

    async def _handle_integrate_frontend_api(self, context: A2ATaskContext, description: str) -> A2ATaskResult:
        framework = self._determine_framework(context, description)
        # Placeholder logic
        api_endpoint = "/api/data" # Extract from description
        js_code = f"""
// JavaScript ({framework}) to integrate with API: {api_endpoint}
async function fetchData() {{
  try {{
    const response = await fetch('{api_endpoint}');
    const data = await response.json();
    console.log('Data fetched:', data);
    // Update UI with data
  }} catch (error) {{
    console.error('Failed to fetch data:', error);
  }}
}}
fetchData();
"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        return A2ATaskResult(
            status="completed",
            artifacts=[A2AArtifact(name="api_integration.js", description=f"JS for API integration with {api_endpoint}", parts=[A2ATextPart(text=js_code)])]
        )