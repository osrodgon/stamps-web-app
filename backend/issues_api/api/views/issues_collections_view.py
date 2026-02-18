from django.db import transaction
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

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
                    if issue_date_value:
                        year_value = issue_date_value.year
                        year, _ = Year.objects.get_or_create(year=year_value)
                    else:
                        # Cannot continue wit a yearless issue, return error response
                        raise ValueError("issue_date")
                    
                    # Extract country
                    country_value = validated_data.get('country')
                    if not country_value or country_value.lower() == "n/a":
                        country_value = "españa"
                    country_value = country_value.strip().capitalize()
                    country, _ = Country.objects.get_or_create(name=country_value)
                        
                    
                    # Extract stamp type
                    stamp_type_value = validated_data.get('stamp_type')
                    if stamp_type_value and stamp_type_value.lower() != "n/a":
                        stamp_type_value = stamp_type_value.strip().capitalize()
                        stamp_type, _ = StampType.objects.get_or_create(name=stamp_type_value)
                    else:
                        stamp_type = None
                        
                    # Extract print type
                    print_type_value = validated_data.get('print_type')
                    if print_type_value and print_type_value.lower() != "n/a":
                        print_type_value = print_type_value.strip().capitalize()   
                        print_type, _ = PrintType.objects.get_or_create(name=print_type_value)
                    else:
                        print_type = None
                        
                    #Extract issue data
                    
                    # Validate issue_name
                    issue_name_value = validated_data.get('issue_name')
                    if not issue_name_value or issue_name_value.lower() == "n/a":
                        raise ValueError("issue_name")
                    issue_name_value = issue_name_value.strip().capitalize()
                    
                    # Validate total_printed
                    total_printed_value = validated_data.get('total_printed')
                    if total_printed_value is not None and total_printed_value < 0:
                        raise ValueError("total_printed")
                    if total_printed_value is None:
                        total_printed_value = 0
                        
                    # Validate perforation
                    perforation_value = validated_data.get('perforation')
                    if not perforation_value or perforation_value.lower() == "n/a":
                        raise ValueError("perforation")
                    perforation_value = perforation_value.strip().capitalize()
                    
                    # Validate description
                    description_value = validated_data.get('description')
                    if description_value is None or description_value.lower() == "n/a":
                        description_value
                            
                    # Validate notes
                    notes_value = validated_data.get('notes')
                    if notes_value is not None and notes_value.lower() == "n/a":
                        notes_value = None
                        
                    # Validate market_value_mnh
                    market_value_mnh_value = validated_data.get('market_value_mnh')
                    if market_value_mnh_value is not None and market_value_mnh_value < 0:
                        raise ValueError("market_value")
                    if market_value_mnh_value is None:
                        market_value_mnh_value = 0.0

                    # Create issue only if combination og year, name and date is unique
                    # Otherwise update the existing one with the new data (except for 
                    # the name, date and year that will remain unchanged)
                    issue, created = Issue.objects.get_or_create(
                        name=issue_name_value,
                        date=issue_date_value,
                        year=year,
                        defaults={
                            'stamp_type': stamp_type,
                            'print_type': print_type,
                            'country': country,
                            'total_printed': total_printed_value,
                            'perforation': perforation_value,
                            'description': description_value,
                            'note': notes_value,
                            'market_value': market_value_mnh_value
                        }
                    )
                    
                    # Validate stamps
                    for stamp in validated_data.get('stamps', []):
                        # Validate colors and create list of color entities
                        color_value = stamp.get('color')
                        color_names = self._parse_colors(color_value)
                        
                        # Validate edifil_code
                        edifil_code_value = stamp.get('edifil_code')
                        if not edifil_code_value:
                            edifil_code_value = "n/a"
                        edifil_code_value = edifil_code_value.strip().capitalize()
                        
                        # Validate motive
                        motive_value = stamp.get('motive')
                        if not motive_value:
                            motive_value = "n/a"
                        motive_value = motive_value.strip().capitalize()
                        
                        # Validate face_value
                        face_value_value = stamp.get('face_value')
                        if not face_value_value:
                            face_value_value = "n/a"
                        face_value_value = face_value_value.strip().capitalize()
                        
                        # Validate amount_printed
                        amount_printed_value = stamp.get('amount_printed')
                        if amount_printed_value is not None and amount_printed_value < 0:
                            raise ValueError("amount_printed")
                        if amount_printed_value is None:
                            amount_printed_value = 0
                            
                        # Validate market_value_mnh
                        market_value_mnh_value = stamp.get('market_value_mnh')
                        if market_value_mnh_value is not None and market_value_mnh_value < 0:
                            market_value_mnh_value = 0.0
                        if market_value_mnh_value is None:
                            market_value_mnh_value = 0.0
                            
                        # Validate description
                        description_value = stamp.get('description')
                        if not description_value:
                            description_value = "n/a"
                        description_value = description_value.strip().capitalize()
                        
                        # Create image path
                        image_path_value = f"{year_value}/{edifil_code_value}.webp" 
                        
                        stamp, _ = Stamp.objects.get_or_create(
                            name = motive_value,
                            issue = issue,
                            edifil_code = edifil_code_value,
                            face_value = face_value_value,
                            description = description_value,
                            market_value = market_value_mnh_value,
                            total_printed = amount_printed_value,
                            image = image_path_value
                        )
                        
                        color_objects = []
                        for color_name in color_names:
                            color, _ = Color.objects.get_or_create(name=color_name)
                            color_objects.append(color)
                        
                        stamp.colors.set(color_objects)    

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