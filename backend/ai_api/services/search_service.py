"""
Search service for AI-powered stamp series extraction.

This module provides web search capabilities to locate stamp series information
from external philatelic catalogs. It integrates with the Serper API (Google Search API)
to find reference URLs for stamp issues, which are then used by the AI service
to gather additional data for series extraction.

The service is specifically designed to search the Spanish philatelic catalog
(catalogodesellos.fesofi.es) to find product pages for stamp issues based on
their name and publication date.

Dependencies:
    - requests: For making HTTP requests to the Serper API
    - common.log.logger: For consistent logging throughout the application
    - _backend.settings: For accessing Serper API configuration

Integration:
    - Used by SeriesExtractionView in the AI workflow
    - Part of the ai_api.services module
    - Works in conjunction with LLMService for complete series extraction
"""

import requests
import json
from typing import Optional

from common.log.logger import Logger
from _backend.settings import SERPER_URL, SERPER_API_KEY


class SearchService(Logger):
    """
    Service class for performing web searches to locate stamp series information.
    
    This service uses the Serper API to search for stamp issues on the Spanish
    philatelic catalog (catalogodesellos.fesofi.es). It constructs targeted search
    queries using stamp name and publication date to find the corresponding product
    page URLs.
    
    The search results are used by the AI service pipeline to gather reference data
    for stamp series extraction and validation.
    
    Attributes:
        Inherits from Logger for consistent application logging
        
    Methods:
        find_series_url: Searches for and returns the URL of a stamp series page
        
    Usage:
        search_service = SearchService()
        url = search_service.find_series_url("Olimpiadas", "1992")
    """
    def find_series_url(self, name: str, date: str) -> Optional[str]:
        """
        Search for and return the URL of a stamp series page from the Spanish philatelic catalog.
        
        This method performs a targeted web search using the Serper API to find product pages
        for specific stamp issues on catalogodesellos.fesofi.es. The search is constructed
        using the stamp issue name and publication date to ensure precise results.
        
        Args:
            name (str): The name of the stamp issue (e.g., "Olimpiadas", "Animales")
            date (str): The publication date of the stamp issue (e.g., "1992", "2023")
            
        Returns:
            Optional[str]:  The URL of the first matching product page if found, otherwise None.
                            Returns None if:
                                - No search results are returned
                                - No organic results contain "/producto/" in the URL
                                - An error occurs during the API request
        
        Raises:
            requests.exceptions.RequestException: If the HTTP request to Serper API fails
            json.JSONDecodeError: If the API response cannot be parsed as JSON
            KeyError: If expected fields are missing from the API response
            
        Example:
            >>> search_service = SearchService()
            >>> url = search_service.find_series_url("Olimpiadas", "1992")
            >>> print(url)  # https://catalogodesellos.fesofi.es/producto/olimpiadas-1992/
            
        Note:
            This method uses a silent failure pattern - exceptions are caught and logged
            internally, with None returned to indicate failure. This allows the calling
            code to handle missing data gracefully without needing try-catch blocks.
        """
        query = f'site:catalogodesellos.fesofi.es "{name}" "{date}"'
        
        payload = json.dumps({
            "q": query,
            "gl": "es",  # Geographic location: Spain for better regional accuracy
        })
    
        headers = {
            'X-API-KEY': SERPER_API_KEY,  # Authentication key from environment variables
            'Content-Type': 'application/json'  # Specify JSON content type
        }
        
        try:
            self.log.debug(f"Sending request to Serper API for query: {query}")
            response = requests.post(SERPER_URL, headers=headers, data=payload)
            
            # Raise an exception for HTTP error status codes (4xx, 5xx)
            response.raise_for_status()
            results = response.json()
            
            # Check if the response contains organic search results
            if "organic" in results:
                # Iterate through organic search results to find product pages
                for item in results["organic"]:
                    link = item.get("link", "")
                    # Look for URLs containing "/producto/" which indicates a product page
                    if "/producto/" in link:
                        return link  # Return the first matching product URL found
                        
        except Exception as e:
            self.log.error(f"Error during Serper API request: {e}")
            
        # Return None if no matching URL was found or if an error occurred
        return None
