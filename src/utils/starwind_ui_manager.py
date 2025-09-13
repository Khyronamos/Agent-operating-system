import logging
import os
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class StarwindUIManager:
    """
    Manager for Starwind UI operations.
    
    This class provides a unified interface for Starwind UI operations,
    using the Starwind UI MCP server.
    """
    
    def __init__(self, mcp_manager):
        """
        Initialize the Starwind UI manager.
        
        Args:
            mcp_manager: The MCP client manager
        """
        self.mcp_manager = mcp_manager
        self.server_name = "starwind-ui"
    
    async def list_components(self) -> List[str]:
        """
        List available UI components.
        
        Returns:
            List of available component types
        """
        logger.debug("Listing available components...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "listComponents",
            {}
        )
        
        return result
    
    async def generate_component(self, component_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a UI component.
        
        Args:
            component_type: Type of component to generate
            params: Parameters for the component
            
        Returns:
            Generated component details
        """
        logger.debug(f"Generating {component_type} component...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "generateComponent",
            {
                "componentType": component_type,
                "params": params
            }
        )
        
        return result
    
    async def preview_component(self, html: str) -> Dict[str, str]:
        """
        Generate a preview URL for a component.
        
        Args:
            html: HTML content of the component
            
        Returns:
            Preview details including URL
        """
        logger.debug("Generating preview URL...")
        
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "previewComponent",
            {
                "html": html
            }
        )
        
        return result
    
    async def generate_landing_page(self, business_name: str, business_type: str, 
                                  description: Optional[str] = None, 
                                  color_scheme: str = "blue",
                                  features: Optional[List[str]] = None,
                                  testimonials: Optional[List[Dict[str, str]]] = None,
                                  contact_info: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Generate a landing page for a business.
        
        Args:
            business_name: Name of the business
            business_type: Type of business
            description: Business description (optional)
            color_scheme: Color scheme (optional, default: "blue")
            features: List of business features (optional)
            testimonials: List of testimonials (optional)
            contact_info: Contact information (optional)
            
        Returns:
            Generated landing page details
        """
        logger.debug(f"Generating landing page for {business_name}...")
        
        # Prepare parameters
        params = {
            "businessName": business_name,
            "businessType": business_type,
            "colorScheme": color_scheme
        }
        
        if description:
            params["description"] = description
        
        if features:
            params["features"] = features
        
        if testimonials:
            params["testimonials"] = testimonials
        
        if contact_info:
            params["contactInfo"] = contact_info
        
        # Generate landing page
        return await self.generate_component("landing-page", params)
    
    async def generate_contact_form(self, business_name: str, 
                                  color_scheme: str = "blue",
                                  fields: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate a contact form for a business.
        
        Args:
            business_name: Name of the business
            color_scheme: Color scheme (optional, default: "blue")
            fields: List of form fields (optional)
            
        Returns:
            Generated contact form details
        """
        logger.debug(f"Generating contact form for {business_name}...")
        
        # Prepare parameters
        params = {
            "businessName": business_name,
            "colorScheme": color_scheme
        }
        
        if fields:
            params["fields"] = fields
        
        # Generate contact form
        return await self.generate_component("contact-form", params)
    
    async def generate_pricing_table(self, business_name: str, 
                                   plans: List[Dict[str, Any]],
                                   color_scheme: str = "blue") -> Dict[str, Any]:
        """
        Generate a pricing table for a business.
        
        Args:
            business_name: Name of the business
            plans: List of pricing plans
            color_scheme: Color scheme (optional, default: "blue")
            
        Returns:
            Generated pricing table details
        """
        logger.debug(f"Generating pricing table for {business_name}...")
        
        # Prepare parameters
        params = {
            "businessName": business_name,
            "plans": plans,
            "colorScheme": color_scheme
        }
        
        # Generate pricing table
        return await self.generate_component("pricing-table", params)
    
    async def generate_service_list(self, business_name: str, 
                                  services: List[Dict[str, Any]],
                                  color_scheme: str = "blue") -> Dict[str, Any]:
        """
        Generate a service list for a business.
        
        Args:
            business_name: Name of the business
            services: List of services
            color_scheme: Color scheme (optional, default: "blue")
            
        Returns:
            Generated service list details
        """
        logger.debug(f"Generating service list for {business_name}...")
        
        # Prepare parameters
        params = {
            "businessName": business_name,
            "services": services,
            "colorScheme": color_scheme
        }
        
        # Generate service list
        return await self.generate_component("service-list", params)
    
    async def generate_testimonial_section(self, business_name: str, 
                                         testimonials: List[Dict[str, str]],
                                         color_scheme: str = "blue") -> Dict[str, Any]:
        """
        Generate a testimonial section for a business.
        
        Args:
            business_name: Name of the business
            testimonials: List of testimonials
            color_scheme: Color scheme (optional, default: "blue")
            
        Returns:
            Generated testimonial section details
        """
        logger.debug(f"Generating testimonial section for {business_name}...")
        
        # Prepare parameters
        params = {
            "businessName": business_name,
            "testimonials": testimonials,
            "colorScheme": color_scheme
        }
        
        # Generate testimonial section
        return await self.generate_component("testimonial-section", params)
    
    async def save_component(self, component_result: Dict[str, Any], output_path: str) -> str:
        """
        Save a generated component to a file.
        
        Args:
            component_result: Component result from generate_component
            output_path: Path to save the component
            
        Returns:
            Path to the saved file
        """
        logger.debug(f"Saving component to {output_path}...")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save HTML to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(component_result["html"])
        
        return output_path
    
    async def generate_and_save_landing_page(self, business_name: str, business_type: str, 
                                           output_path: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a landing page and save it to a file.
        
        Args:
            business_name: Name of the business
            business_type: Type of business
            output_path: Path to save the landing page
            **kwargs: Additional parameters for generate_landing_page
            
        Returns:
            Dictionary with component details and file path
        """
        logger.debug(f"Generating and saving landing page for {business_name}...")
        
        # Generate landing page
        result = await self.generate_landing_page(business_name, business_type, **kwargs)
        
        # Save to file
        file_path = await self.save_component(result, output_path)
        
        return {
            "component": result,
            "file_path": file_path
        }
