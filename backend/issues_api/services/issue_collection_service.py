from django.db import transaction
from artists_api.models import Artist
from paper_types_api.models import PaperType
from printers_api.models import Printer
from stamps_api.models import Stamp
from colors_api.models import Color
from issues_api.models import Issue
from countries_api.models import Country
from print_types_api.models import PrintType
from stamp_types_api.models import StampType
from years_api.models import Year


class IssueCollectionService:
    """
    Service class for handling the creation of issues with all related entities.
    
    This service encapsulates the business logic for creating complete issue entries
    including all related entities such as year, stamp type, print type, country, and colors.
    """
    
    def create_issue_collection(self, validated_data: dict) -> dict:
        """
        Creates a complete issue entry with all related entities.
        
        Args:
            validated_data: The validated data from the request serializer
            
        Returns:
            dict: A dictionary containing the created issue information
            
        Raises:
            ValueError: If required data is missing or invalid
            Exception: If any database operation fails
        """
        with transaction.atomic():
            # Create all related entities first
            related_entities = self._create_related_entities(validated_data)
            
            # Create the main issue entity
            issue = self._create_issue_entity(validated_data, related_entities)
            
            # Process and create stamps
            self._process_stamps(validated_data.get('stamps', []), issue, related_entities['year'])
            
            return {
                "issue_name": issue.name,
                "issue_date": issue.date
            }
    
    def _create_related_entities(self, validated_data: dict) -> dict:
        """
        Create all related entities (Year, Country, StampType, etc.) needed for the issue.
        
        Args:
            validated_data: The validated data from the request serializer
            
        Returns:
            dict: Dictionary containing all created related entities
        """
        # Extract and create year
        issue_date_value = validated_data.get('issue_date')
        if not issue_date_value:
            raise ValueError("issue_date is required to create a Year record")
        year_value = issue_date_value.year
        year_obj, _ = Year.objects.get_or_create(year=year_value)
        
        # Extract and create country
        country_value = (validated_data.get('country') or "españa").strip()
        country_value = "españa" if country_value.lower() == "n/a" else country_value.capitalize()
        country_obj, _ = Country.objects.get_or_create(name=country_value)
        
        # Extract and create stamp type
        stamp_type_obj = self._create_entity_if_valid(
            validated_data.get('stamp_type'),
            StampType,
            'stamp_type'
        )
        
        # Extract and create print type
        print_type_obj = self._create_entity_if_valid(
            validated_data.get('print_type'),
            PrintType,
            'print_type'
        )
        
        # Extract and create artist
        artist_obj = self._create_entity_if_valid(
            validated_data.get('artist'),
            Artist,
            'artist'
        )
        
        # Extract and create printer
        printer_obj = self._create_entity_if_valid(
            validated_data.get('printer'),
            Printer,
            'printer'
        )
        
        # Extract and create paper type
        paper_type_obj = self._create_entity_if_valid(
            validated_data.get('paper_type'),
            PaperType,
            'paper_type'
        )
        
        return {
            'year': year_obj,
            'country': country_obj,
            'stamp_type': stamp_type_obj,
            'print_type': print_type_obj,
            'artist': artist_obj,
            'printer': printer_obj,
            'paper_type': paper_type_obj
        }
    
    def _create_entity_if_valid(self, value: str, model_class, field_name: str):
        """
        Create an entity if the value is valid, otherwise return None.
        
        Args:
            value: The value to validate and create entity from
            model_class: The Django model class to create
            field_name: The field name for error messages
            
        Returns:
            The created entity object or None if invalid
        """
        if value and value.strip().lower() != "n/a":
            value = value.strip().capitalize()
            obj, _ = model_class.objects.get_or_create(name=value)
            return obj
        return None
    
    def _create_issue_entity(self, validated_data: dict, related_entities: dict) -> Issue:
        """
        Create the main Issue entity with all validated data.
        
        Args:
            validated_data: The validated data from the request serializer
            related_entities: Dictionary containing all related entities
            
        Returns:
            Issue: The created or updated Issue instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required issue data
        issue_name_value = (validated_data.get('issue_name') or ('n/a')).strip()
        if not issue_name_value or issue_name_value.lower() == "n/a":
            raise ValueError("issue_name")
        
        issue_date_value = validated_data.get('issue_date')
        if not issue_date_value:
            raise ValueError("issue_date")
        
        # Validate optional fields with defaults
        total_printed_value = validated_data.get('total_printed') or 0
        if total_printed_value < 0:
            raise ValueError("total_printed")
        
        perforation_value = (validated_data.get('perforation') or "n/a").strip()
        if perforation_value.lower() != "n/a":
            perforation_value = perforation_value.capitalize()
        
        description_value = (validated_data.get('description') or "n/a").strip()
        if description_value.lower() == "n/a":
            description_value = None
        
        notes_value = (validated_data.get('notes') or "n/a").strip()
        if notes_value.lower() == "n/a":
            notes_value = None
        
        market_value_mnh_value = validated_data.get('market_value_mnh') or 0
        if market_value_mnh_value < 0:
            raise ValueError("market_value_mnh")
        
        market_value_used_value = validated_data.get('market_value_used') or 0
        if market_value_used_value < 0:
            raise ValueError("market_value_used")
        
        # Create or update issue
        issue, _ = Issue.objects.get_or_create(
            name=issue_name_value,
            date=issue_date_value,
            year=related_entities['year'],
            defaults={
                'stamp_type': related_entities['stamp_type'],
                'print_type': related_entities['print_type'],
                'country': related_entities['country'],
                'total_printed': total_printed_value,
                'perforation': perforation_value,
                'description': description_value,
                'note': notes_value,
                'market_value_mnh': market_value_mnh_value,
                'market_value_used': market_value_used_value,
                'artist': related_entities['artist'],
                'printer': related_entities['printer'],
                'paper_type': related_entities['paper_type']
            }
        )
        
        return issue
    
    def _process_stamps(self, stamps_data: list, issue: Issue, year_obj: Year):
        """
        Process and create stamp entities with their associated colors.
        
        Args:
            stamps_data: List of stamp data from the request
            issue: The Issue instance to associate stamps with
            year_obj: The Year instance for image path generation
        """
        for stamp_data in stamps_data:
            # Parse colors
            color_value = stamp_data.get('color') or "n/a"
            color_names = self._parse_colors(color_value)
            
            # Validate required stamp fields
            edifil_code_value = (stamp_data.get('edifil_code') or "n/a").strip()
            fesofi_code_value = (stamp_data.get('fesofi_code') or "n/a").strip()
            motive_value = (stamp_data.get('motive') or "n/a").strip()
            face_value_value = (stamp_data.get('face_value') or "n/a").strip()
            
            # Validate optional fields
            amount_printed_value = stamp_data.get('amount_printed') or 0
            if amount_printed_value < 0:
                raise ValueError("amount_printed")
            
            market_value_mnh_value = stamp_data.get('market_value_mnh') or 0
            if market_value_mnh_value < 0:
                market_value_mnh_value = 0.0
            
            market_value_used_value = stamp_data.get('market_value_used') or 0
            if market_value_used_value < 0:
                market_value_used_value = 0.0
            
            description_value = (stamp_data.get('description') or "n/a").strip()
            if description_value == 'n/a':
                description_value = None
            
            # Create image path
            image_path_value = f"{year_obj.year}/{edifil_code_value}.webp"
            
            # Create or update stamp
            stamp, _ = Stamp.objects.get_or_create(
                edifil_code=edifil_code_value,
                fesofi_code=fesofi_code_value,
                defaults={
                    'name': motive_value,
                    'issue': issue,
                    'face_value': face_value_value,
                    'description': description_value,
                    'market_value_mnh': market_value_mnh_value,
                    'market_value_used': market_value_used_value,
                    'total_printed': amount_printed_value,
                    'image': image_path_value
                }
            )
            
            # Create and associate colors
            color_objects = []
            for color_name in color_names:
                color_obj, _ = Color.objects.get_or_create(name=color_name)
                color_objects.append(color_obj)
            
            stamp.colors.set(color_objects)
    
    def _parse_colors(self, color_string: str) -> list:
        """
        Parse color string into a list of capitalized colors.
        Handles formats like:
        - "rojo" -> ["Rojo"]
        - "rojo, verde y azul" -> ["Rojo", "Verde", "Azul"]
        - "Rojo,Verde" -> ["Rojo", "Verde"]
        
        Args:
            color_string: The color string to parse
            
        Returns:
            list: List of capitalized color names
        """
        if not color_string or color_string.lower() == 'n/a':
            return []
        
        # Replace " y " (Spanish "and") with comma
        color_string = color_string.replace(' y ', ',').replace(' Y ', ',')
        
        # Split by comma
        colors = color_string.split(',')
        
        # Strip whitespace and capitalize each color
        colors = [color.strip().capitalize() for color in colors]
        
        # Filter out empty strings
        return [c for c in colors if c]