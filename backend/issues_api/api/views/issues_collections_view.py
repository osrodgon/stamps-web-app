from django.db import transaction
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

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
from common.api.messages import Messages
from common.log.logger import Logger
from common.core.schemas import standardized_response
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from issues_api.api.serializers.issue_collection_request_serializer import IssueCollectionRequestSerializer
from issues_api.api.serializers.issue_collection_response_serializer import IssueCollectionResponseSerializer

@extend_schema(tags=['Database Management'])
class IssuesCollectionsView(Logger, APIView):
    """
    API view for handling the creation of issues with all related entities.
    """
    @extend_schema(
        operation_id="create_issue_collections",
        summary="Creates a new issue with all related entities in a single request",
        description="Creates a complete issue entry in the database. This includes all related entities such as year, stamp type, print type, location, country, and color. The endpoint expects a comprehensive payload containing all necessary information to create the issue and its related entities in a single request.",
        request=IssueCollectionRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response( 
                IssueCollectionResponseSerializer,
                name="IssueCollectionsCreated",
                description="The issue was created successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="IssueCollectionsCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                GenericResponseSerializer,
                name="IssueCollectionsCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """
        Handles POST requests to create a new issue with all related entities.

        Args:
            request: The incoming HTTP request containing the issue and related entities data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A Response object with the result of the creation operation.
        """
        self.log.debug(Messages.Post.create_one("issue collection", f"{str(request.data)[:35]}..."))
        
        collection = IssueCollectionRequestSerializer(data=request.data)
        
        if collection.is_valid():
            validated_data = collection.validated_data
            
            try:
                # Start a transaction to ensure atomicity of the creation process
                with transaction.atomic():
                    # Extract year
                    issue_date_value = validated_data.get('issue_date')
                    if not issue_date_value:
                        raise ValueError("issue_date is required to create a Year record")
                    year_value = issue_date_value.year
                    year_obj, _ = Year.objects.get_or_create(year=year_value)
                    
                    # Extract country
                    country_value = (validated_data.get('country') or "españa").strip()
                    country_value = "españa" if country_value.lower() == "n/a" else country_value.capitalize()
                    country_obj, _ = Country.objects.get_or_create(name=country_value)
                        
                    
                    # Extract stamp type
                    stamp_type_value = (validated_data.get('stamp_type') or 'n/a').strip()
                    if stamp_type_value and stamp_type_value.lower() != "n/a":
                        stamp_type_value = stamp_type_value.capitalize()
                        stamp_type_obj, _ = StampType.objects.get_or_create(name=stamp_type_value)
                    else:
                        stamp_type_obj = None
                        
                    # Extract print type
                    print_type_value = (validated_data.get('print_type') or 'n/a').strip()
                    if print_type_value and print_type_value.lower() != "n/a":
                        print_type_value = print_type_value.capitalize()   
                        print_type_obj, _ = PrintType.objects.get_or_create(name=print_type_value)
                    else:
                        print_type_obj = None
                        
                    #Extract issue data
                    
                    # Validate issue_name
                    issue_name_value = (validated_data.get('issue_name') or ('n/a')).strip()
                    if not issue_name_value or issue_name_value.lower() == "n/a":
                        raise ValueError("issue_name")
                    
                    # Validate total_printed
                    total_printed_value = validated_data.get('total_printed') or 0
                    if total_printed_value < 0:
                        raise ValueError("total_printed")
                        
                    # Validate perforation
                    perforation_value = (validated_data.get('perforation') or "n/a").strip()
                    if perforation_value.lower() != "n/a":
                        perforation_value = perforation_value.capitalize()
                    
                    # Validate description
                    description_value = (validated_data.get('description') or "n/a").strip()
                    if description_value.lower() == "n/a":
                        description_value = None
                            
                    # Validate notes
                    notes_value = (validated_data.get('notes') or "n/a").strip()
                    if notes_value.lower() == "n/a":
                        notes_value = None
                        
                    # Validate market_value_mnh
                    market_value_mnh_value = validated_data.get('market_value_mnh') or 0
                    if market_value_mnh_value < 0:
                        raise ValueError("market_value")
                        
                    # Validate market_value_used
                    market_value_used_value = validated_data.get('market_value_used') or 0
                    if market_value_used_value < 0:
                        raise ValueError("market_value")
                        
                    # Validate artist
                    artist_value = (validated_data.get('artist') or "n/a").strip()
                    if artist_value and artist_value.lower() != "n/a":
                        artist_obj, _ = Artist.objects.get_or_create(name=artist_value) 
                    else:
                        artist_obj = None
                        
                    # Validate printer
                    printer_value = (validated_data.get('printer') or "n/a").strip()
                    if printer_value and printer_value.lower() != "n/a":
                        printer_obj, _ = Printer.objects.get_or_create(name=printer_value)
                    else:
                        printer_obj = None
                        
                    # Validate paper_type
                    paper_type_value = (validated_data.get('paper_type') or "n/a").strip()
                    if paper_type_value and paper_type_value.lower() != "n/a":
                        paper_type_value = paper_type_value.strip().capitalize()
                        paper_type_obj, _ = PaperType.objects.get_or_create(name=paper_type_value)
                    else:
                        paper_type_obj = None
                        
                    # Create issue only if combination of year, name and date is unique
                    # Otherwise update the existing one with the new data (except for 
                    # the name, date and year that will remain unchanged)
                    issue, created = Issue.objects.get_or_create(
                        name=issue_name_value,
                        date=issue_date_value,
                        year=year_obj,
                        defaults={
                            'stamp_type': stamp_type_obj,
                            'print_type': print_type_obj,
                            'country': country_obj,
                            'total_printed': total_printed_value,
                            'perforation': perforation_value,
                            'description': description_value,
                            'note': notes_value,
                            'market_value_mnh': market_value_mnh_value,
                            'market_value_used': market_value_used_value,
                            'artist': artist_obj,
                            'printer': printer_obj,
                            'paper_type': paper_type_obj
                        }
                    )
                    
                    # Validate stamps
                    for stamp_obj in validated_data.get('stamps', []):
                        # Validate colors and create list of color entities
                        color_value = stamp_obj.get('color') or "n/a"
                        color_names = self._parse_colors(color_value)
                        
                        # Validate edifil_code
                        edifil_code_value = (stamp_obj.get('edifil_code') or "n/a").strip()
                        
                        #validate fesofi_code
                        fesofi_code_value = (stamp_obj.get('fesofi_code') or "n/a").strip()
                        
                        # Validate motive
                        motive_value = (stamp_obj.get('motive') or "n/a").strip()
                        
                        # Validate face_value
                        face_value_value = (stamp_obj.get('face_value') or "n/a").strip()
                        
                        # Validate amount_printed
                        amount_printed_value = stamp_obj.get('amount_printed') or 0
                        if amount_printed_value < 0:
                            raise ValueError("amount_printed")
                            
                        # Validate market_value_mnh
                        market_value_mnh_value = stamp_obj.get('market_value_mnh') or 0
                        if market_value_mnh_value < 0:
                            market_value_mnh_value = 0.0

                        # Validate market_value_used
                        market_value_used_value = stamp_obj.get('market_value_used') or 0
                        if market_value_used_value < 0:
                            market_value_used_value = 0.0
                        
                        # Validate description
                        description_value = (stamp_obj.get('description') or "n/a").strip()
                        if description_value == 'n/a':
                            description_value = None
                        
                        # Create image path
                        image_path_value = f"{year_value}/{edifil_code_value}.webp" 
                        
                        # Create stamp
                        stamp_obj, _ = Stamp.objects.get_or_create(
                            edifil_code = edifil_code_value,
                            fesofi_code = fesofi_code_value,
                            defaults = {
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
                        
                        # Create color entities and associate them with the stamp
                        color_objects = []
                        for color_name in color_names:
                            color_obj, _ = Color.objects.get_or_create(name=color_name)
                            color_objects.append(color_obj)
                        
                        stamp_obj.colors.set(color_objects)    

                    # Final step: create the issue with all related entities
                    self.log.debug(Messages.Post.created_one("issue collection", issue_name_value))
                    issue_collection = {
                        "issue_name": issue_name_value,
                        "issue_date": issue_date_value
                    }
                    return Response(
                        data=IssueCollectionResponseSerializer(issue_collection).data,
                        status=status.HTTP_201_CREATED
                    )
            except Exception as e:
                self.log.error(Messages.failed())
                return Response(
                    data=GenericResponseSerializer(GenericResponse([str(e)])).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        self.log.warning(Messages.Post.validation_failed("issue", collection.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(collection.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )
        
    def _parse_colors(self, color_string: str) -> list:
        """
        Parse color string into a list of capitalized colors.
        Handles formats like:
        - "rojo" -> ["Rojo"]
        - "rojo, verde y azul" -> ["Rojo", "Verde", "Azul"]
        - "Rojo,Verde" -> ["Rojo", "Verde"]
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