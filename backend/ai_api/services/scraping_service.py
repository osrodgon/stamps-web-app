"""
Web scraping service for AI-powered stamp series extraction.

This module provides web scraping capabilities to gather detailed information
about stamp series from the Spanish philatelic catalog (catalogodesellos.fesofi.es).
It extracts structured data from product pages to provide context for the AI models.

The service is designed to work in conjunction with the SearchService and LLMService
to create a complete data gathering pipeline for stamp series information.

Dependencies:
    - requests: For making HTTP requests to the philatelic catalog
    - beautifulsoup4: For parsing HTML content and extracting structured data
    - common.log.logger: For consistent application logging

Integration:
    - Used by SeriesExtractionView in the AI workflow
    - Part of the ai_api.services module
    - Works with SearchService to find URLs and LLMService to process data
"""
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from ai_api.sources.errors import SourceError
from ai_api.sources.http import HttpClient, get_client
from ai_api.text import DESCRIPTION_LIMIT, snippet
from common.log.logger import Logger


class ScrapingService(Logger):
    """
    Service responsible for scraping web content to gather context for the LLM.
    
    This service extracts detailed information from stamp product pages on the
    Spanish philatelic catalog. It performs three main functions:
    1. Fetching URLs and extracting related links within a series
    2. Scraping detailed content from multiple stamp pages
    3. Cleaning and structuring the scraped data for AI processing
    
    All the fetching goes through the shared `HttpClient` (allowlist, timeouts,
    per-host limit and cache), and the pages of a series are fetched in parallel
    up to that limit: a 57-stamp series is 57 sequential requests otherwise.
    
    Attributes:
        client (HttpClient): the shared client, or the one a test injects
        
    Usage:
        scraping_service = ScrapingService()
        links = scraping_service.extract_links("https://catalogodesellos.fesofi.es/producto/series/")
        data = scraping_service.scrape_content(links)
        cleaned_data = scraping_service.clean_scraped_data(data)
    """

    def __init__(self, client: Optional[HttpClient] = None) -> None:
        """Take the shared HTTP client, or the one a test injects."""
        super().__init__()
        self.client = client or get_client()

    def _fetch_url(self, url: str) -> str:
        """
        Private helper method to perform HTTP GET requests with error handling.
        
        This method fetches the HTML content through the shared client, so the
        allowlist, the timeout and the retries apply here too.
        
        Args:
            url (str): The URL to fetch content from.
            
        Returns:
            str: The HTML content of the page if successful, empty string otherwise.
            
        Note:
            Failures are logged and turned into an empty string: a missing page
            must not abort the rest of the series.
            
        Note:
            This is a private method used internally by other methods in the class.
            It logs errors using the inherited Logger functionality.
        """
        try:
            response = self.client.get(url)
        except SourceError as e:
            self.log.error(f"Error fetching URL {url}: {str(e)}")
            return ""

        if response.status_code >= 400:
            self.log.error(f"Error fetching URL {url}: HTTP {response.status_code}")
            return ""

        return response.text

    def extract_links(self, url: str) -> List[str]:
        """
        Fetches a URL and extracts all relevant internal links from a stamp series page.
        
        This method is specifically designed to find related stamp pages within a series.
        It looks for links that point to other stamps in the same series, which are typically
        found in a section labeled "resto valores serie" (remaining values of the series).
        
        Args:
            url (str): The URL of the main stamp series page to extract links from.
            
        Returns:
            List[str]:  A sorted list of unique URLs pointing to related stamp pages
                        within the same series, including the original URL.
                        Returns an empty list if the page cannot be fetched or parsed.

        Example:
            >>> service = ScrapingService()
            >>> links = service.extract_links("https://catalogodesellos.fesofi.es/producto/olimpiadas-1992/")
            >>> print(links)  # Returns list of related stamp URLs in the series
            
        Note:
            The method includes URL cleaning to ensure consistency (removes query parameters
            and trailing slashes) and uses a set to avoid duplicate URLs. It prioritizes
            finding links in the specific "resto valores serie" section but falls back to
            searching the entire page if that section is not found.
        """
        html_content = self._fetch_url(url)
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        related_section = None
        
        # Look for the heading that typically introduces the section
        heading = soup.find(lambda tag: 'resto valores serie' in tag.text.lower())
        if heading:
            # Usually the links are in the next sibling div or the parent container
            related_section = heading.find_parent()
        
        # Use a set to avoid duplicates
        found_urls = set() 
        
        # If we found the specific section, look there first
        search_area = related_section if related_section else soup
        
        for a in search_area.find_all('a', href=True):
            href = a['href']
            # Filter: Must start with 'https://catalogodesellos.fesofi.es/producto' and must be an absolute URL
            if href.startswith('https://catalogodesellos.fesofi.es/producto/'):
                # Clean the URL (remove trailing slashes or queries for consistency)
                clean_url = href.split('?')[0].rstrip('/') + '/'
                found_urls.add(clean_url)
                
        # Always add the original URL
        found_urls.add(url)
        
        return sorted(found_urls)
            
    def scrape_content(self, urls: List[str]) -> List[dict]:
        """
        Visits a list of URLs and extracts structured content from each stamp page.
        
        This method scrapes detailed information from multiple stamp product pages,
        extracting key data points such as title, description, and technical specifications.
        The extracted data is structured into dictionaries for each stamp and returned
        as a list for further processing.
        
        Args:
            urls (List[str]):   A list of URLs pointing to stamp product pages to scrape.
                                Each URL should point to a different stamp in the same series.

        Returns:
            List[dict]: A list of dictionaries, where each dictionary contains
                        structured data for one stamp. Each dictionary includes:
                        - url: The original URL
                        - titulo: The stamp title
                        - descripcion: The stamp description
                        - Various technical fields (e.g., 'date', 'facial', etc.)

        Example:
            >>> service = ScrapingService()
            >>> urls = ["https://catalogodesellos.fesofi.es/producto/stamp1/", ...]
            >>> data = service.scrape_content(urls)
            >>> print(data[0]['titulo'])  # Access title of first stamp
            
        Note:
            The method includes error handling - if a URL fails to load or parse,
            it will be skipped and the method will continue processing the remaining URLs.
            This ensures that partial failures don't break the entire scraping process.
        """
        unique_urls = list(dict.fromkeys(urls))
        pages = self._fetch_many(unique_urls)

        extracted_data = []
        for url in unique_urls:
            html = pages.get(url) or ""
            if not html:
                continue
            stamp_data = self._parse_stamp(url, html)
            if stamp_data is not None:
                extracted_data.append(stamp_data)

        return extracted_data

    def _fetch_many(self, urls: List[str]) -> Dict[str, str]:
        """Fetch the pages of a series in parallel, bounded by the per-host limit."""
        if not urls:
            return {}

        workers = max(1, min(len(urls), self.client.per_host_limit))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            bodies = list(pool.map(self._fetch_url, urls))

        return dict(zip(urls, bodies))

    def _parse_stamp(self, url: str, html: str) -> Optional[dict]:
        """Read one product page; None when the HTML does not parse."""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            stamp_data = {"url": url}

            title = soup.find('h1', class_='product_title')
            stamp_data['titulo'] = title.get_text(strip=True) if title else None

            desc_panel = soup.find('div', id='paneldescription')
            if desc_panel:
                stamp_data['descripcion'] = desc_panel.get_text(strip=True)

            tech_panel = soup.find('div', id='paneladditional_information')
            if tech_panel:
                table = tech_panel.find('table')
                if table:
                    for row in table.find_all('tr'):
                        label = row.find('th')
                        value = row.find('td')
                        if label and value:
                            key = label.get_text(strip=True).replace(':', '').lower()
                            stamp_data[key] = value.get_text(strip=True)

            return stamp_data

        except Exception as e:
            self.log.error(f"Error scraping data from {url}: {e}")
            return None
    
    @staticmethod
    def _snippet(text: str) -> str:
        """Return the description, cut only when it is longer than the limit."""
        return snippet(text)

    def clean_scraped_data(self, scraped_data: List[dict]) -> dict:
        """
        Cleans and structures scraped stamp data for efficient AI processing.
        
        This method processes raw scraped data from multiple stamp pages and transforms
        it into a structured format optimized for AI model consumption. It separates
        common series-level information from unique stamp-level details and applies
        data cleaning techniques to reduce token usage while preserving essential information.
        
        Args:
            scraped_data (List[dict]):  Raw scraped data from multiple stamp pages.
                                        Each dictionary should contain fields like 'titulo',
                                        'descripcion', 'año de emisión', 'facial', etc.

        Returns:
            dict: A structured dictionary with two main sections:
                    - 'serie_info': Dictionary containing common fields shared across
                                    all stamps in the series (e.g., 'año de emisión',
                                    'título serie', 'imprenta', etc.)
                    - 'stamps': List of dictionaries, each containing unique information
                                for individual stamps in the series, including:
                                - edifil: Edifil catalog number
                                - fesofi: Fesofi catalog number  
                                - motivo: Stamp motif/description
                                - facial: Face value
                                - color: Stamp color
                                - dentado: Perforation type
                                - formato: Format/size
                                - desc_snippet: The description, cut at DESCRIPTION_LIMIT characters
                            with an ellipsis only when it does not fit

        Example:
            >>> service = ScrapingService()
            >>> raw_data = service.scrape_content(urls)
            >>> cleaned = service.clean_scraped_data(raw_data)
            >>> print(cleaned['serie_info']['título serie'])  # Access series title
            >>> print(cleaned['stamps'][0]['motivo'])  # Access first stamp's motif
            
        Note:
            This method includes several optimization techniques:
            - Identifies and extracts common fields to avoid repetition
            - Caps very long descriptions (see DESCRIPTION_LIMIT) instead of
              trimming every one of them
            - Standardizes field names for consistency
            - Handles missing data gracefully with default values
        """
        if not scraped_data:
            return {}
        
        self.log.debug("Cleaning scraped data")
        self.log.debug(scraped_data)

        # 1. Identify common fields (constants)
        # We compare the first stamp to the rest
        first_stamp = scraped_data[0]
        common_fields = {}
        keys_to_check = ['año de emisión', 'fecha de emisión', 'título serie', 
                        'imprenta', 'impresión', 'tipo de correo', 'valores de la serie', 'grabador', 'tirada', 'dentado']
        
        new_keys = ['year', 'issue_date', 'issue_name', 'printer', 'print_type', 'stamp_type', 'series_values', 
                    'engraver', 'print_run', 'perforation']
        
        for index, key in enumerate(keys_to_check):
            # If the value is the same in all stamps, it's a constant
            if all(s.get(key) == first_stamp.get(key) for s in scraped_data):
                common_fields[new_keys[index]] = first_stamp.get(key)
            else:
                # Special case for 'fecha de emisión' - if it varies, we can still take the 
                # earliest date as a common field
                if key == 'fecha de emisión':
                    self.log.debug(f"Field '{key}' varies across stamps, checking for earliest date.")
                    dates = [s.get(key) for s in scraped_data if s.get(key)]
                    if dates:
                        common_fields['issue_date'] = min(dates)  # Take the earliest date
                        
                # Sepcial case for 'título serie'. If it varies, we can still take the
                # earliest name as common field
                if key == 'título serie':
                    self.log.debug(f"Field '{key} varies across stamps, checking for earliest issue name.")
                    names = [s.get(key) for s in scraped_data if s.get(key)]
                    if names:
                        common_fields['issue_name'] = min(names)  # Take the earliest issue name
        

        # 2. Extract unique stamp data
        unique_stamps = []
        for s in scraped_data:
            stamp_entry = {
                "edifil_code": s.get("número edifil"),
                "fesofi_code": s.get("número fesofi"),
                "motive": s.get("motivo sello"),
                "face_value": s.get("facial"),
                "color": s.get("color"),
                "perforation": s.get("dentado"),
                "total_print_run": s.get("tirada"),
                "format": s.get("formato"),
                "desc_snippet": self._snippet(s.get("descripcion", "")),
            }
            unique_stamps.append(stamp_entry)

        return {
            "serie_info": common_fields,
            "stamps": unique_stamps
        }
