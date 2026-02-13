from logging import config
import os
import json
import re
from typing import Dict, Any, Optional
from _backend.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME
from google import genai
from google.genai import types

from common.log.logger import Logger
from ai_manager.services.prompts import SERIES_RESEARCH_PROMPT_TEMPLATE

class StampResearchService(Logger):
    """
    Service for performing AI-powered research on stamp series using Google Gemini.
    
    This service handles the integration with Google Gemini API to research
    stamp series information based on issue name, date, and optional Edifil number.
    """
    
    def __init__(self):
        """
        Initialize the StampResearchService.
        
        Sets up Google Gemini API configuration and loads the research prompt template.
        """
        super().__init__()
        
        # Configure Google Gemini API
        api_key = GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        if not GEMINI_MODEL_NAME:
            raise ValueError("GEMINI_MODEL_NAME environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        
        # Create the configuration
        self.generation_config = types.GenerateContentConfig(
            temperature=0.0,
            top_p=1.0,
            top_k=1,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
        
        # Load the research prompt template
        self.prompt_template = SERIES_RESEARCH_PROMPT_TEMPLATE
    
    def _format_prompt(self, issue_name: str, issue_date: str, edifil_start_number: Optional[str]) -> str:
        """
        Format the prompt template with the provided parameters.
        
        Args:
            issue_name: Name of the stamp series
            issue_date: Publication date of the series
            edifil_start_number: Starting Edifil catalog number (optional)
            
        Returns:
            Formatted prompt string with variables replaced.
        """
        # Prepare the Edifil number for the prompt
        edifil_display = edifil_start_number if edifil_start_number else "n/a"
        
        formatted_prompt = self.prompt_template.replace(
            "{{ issue_name }}", issue_name
        ).replace(
            "{{ issue_date }}", issue_date
        ).replace(
            "{{ edifil_start_number }}", edifil_display
        )
        
        self.log.debug(f"Formatted prompt for series: {issue_name}")
        return formatted_prompt
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        Clean the AI response text by removing markdown code blocks.
        
        Args:
            response_text: Raw response text from the AI model.
            
        Returns:
            Cleaned JSON string.
        """
        # Use regex to find the JSON block within markdown code fences or standalone
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Fallback: find the first '{' and the last '}'
        start = response_text.find('{')
        end = response_text.rfind('}')
        
        if start != -1 and end != -1:
            return response_text[start:end+1]
            
        return response_text.strip()

    def _sanitize_response_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize response data to ensure compatibility with serializers.
        Converts None values to empty strings for text fields.
        """
        # Text fields that should be strings (not None)
        text_fields = [
            'description', 'artist', 'printer', 'print_type', 
            'perforation', 'paper_type', 'stamp_type', 'notes'
        ]
        
        for field in text_fields:
            if field in data and data[field] is None:
                data[field] = "n/a"
                
        # Sanitize stamps list
        if 'stamps' in data and isinstance(data['stamps'], list):
            stamp_text_fields = ['edifil_code', 'face_value', 'description', 'color']
            for stamp in data['stamps']:
                if isinstance(stamp, dict):
                    for field in stamp_text_fields:
                        if field in stamp and stamp[field] is None:
                            stamp[field] = "n/a"
                            
        return data
    
    def _validate_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Validate and parse the AI response.
        
        Args:
            response_text: Raw response text from the AI model
            
        Returns:
            Parsed JSON response as a dictionary
            
        Raises:
            ValueError: If the response cannot be parsed as JSON or is invalid
        """
        try:
            # Parse the JSON response
            cleaned_text = self._clean_json_response(response_text) 
            response_data = json.loads(cleaned_text)
            
            # Sanitize data (handle nulls for text fields)
            response_data = self._sanitize_response_data(response_data)
            
            # Validate required fields
            required_fields = ['confidence_score', 'confidence_score_reasons', 'description', 'issue_date', 'artist', 
                                'printer', 'print_type', 'perforation', 'paper_type', 
                                'stamp_type', 'notes', 'total_printed', 'market_value_mnh', 
                                'market_value_used', 'stamps']
            
            for field in required_fields:
                if field not in response_data:
                    raise ValueError(f"Missing required field in AI response: {field}")
            
            # Validate data types
            if not isinstance(response_data['confidence_score'], int) or not (0 <= response_data['confidence_score'] <= 100):
                raise ValueError("confidence_score must be an integer between 0 and 100")
            
            if not isinstance(response_data['confidence_score_reasons'], list):
                raise ValueError("confidence_score_reasons must be a list")
            
            if not isinstance(response_data['stamps'], list):
                raise ValueError("stamps must be a list")
            
            self.log.debug("AI response validation successful")
            return response_data
            
        except json.JSONDecodeError as e:
            self.log.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from AI: {e}")
        except Exception as e:
            self.log.error(f"AI response validation failed: {e}")
            raise ValueError(f"Invalid AI response format: {e}")
    
    def research_series(
        self, 
        issue_name: str, 
        issue_date: str, 
        edifil_start_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform AI research on a stamp series.
        
        Args:
            issue_name: Name of the stamp series to research
            issue_date: Publication date of the series (YYYY-MM-DD format)
            edifil_start_number: Starting Edifil catalog number (optional)
            
        Returns:
            Dictionary containing the research results in the specified format
            
        Raises:
            ValueError: If required parameters are invalid or AI response is invalid
            Exception: If the AI service call fails
        """
        self.log.info(f"Starting AI research for series: {issue_name} ({issue_date})")
        
        # Validate input parameters
        if not issue_name or not issue_name.strip():
            raise ValueError("issue_name is required and cannot be empty")
        
        if not issue_date:
            raise ValueError("issue_date is required")
        
        try:
            # Format the prompt with the provided parameters
            prompt = self._format_prompt(issue_name, issue_date, edifil_start_number)
            
            # Call the AI model
            self.log.debug("Sending request to Google Gemini API")
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=self.generation_config
            )
            
            if not response or not response.text:
                raise ValueError("Empty response from AI service")
            
            self.log.debug(f"Received AI response (length: {len(response.text)})")
            
            # Validate and parse the response
            result = self._validate_ai_response(response.text)
            
            self.log.info(f"AI research completed successfully for series: {issue_name}")
            return result
            
        except Exception as e:
            self.log.error(f"AI research failed for series {issue_name}: {str(e)}")
            raise Exception(f"Research service error: {str(e)}")
