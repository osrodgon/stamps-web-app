from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from artists_api.models import Artist
from artists_api.api.serializers.artist_response_serializer import ArtistResponseSerializer
from artists_api.api.serializers.artist_request_serializer import ArtistRequestSerializer

class ArtistsView(Logger, APIView):
    """Manages bulk API operations for Artist instances.

    This view handles the retrieval of all artists (GET) and the creation
    of a new artist (POST).
    """
    serializer_class = ArtistResponseSerializer
    
    @extend_schema(
        operation_id="list_artists",
        tags=['Database Management'],
        summary="List All Artists",
        description="Retrieves a list of all artist entries currently stored in the database.",
        responses={
            200: standardized_response(
                ArtistResponseSerializer, 
                name="ArtistsRetrieved",
                description="A list of artists was successfully retrieved.",
                many=True
                ),
            403: standardized_response(
                ArtistResponseSerializer,
                name="ArtistsForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve all artists.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response:   A DRF Response object containing a list of all serialized
                        artist objects and a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("artists"))
        artists = Artist.objects.all()
        self.log.debug(Messages.Get.retrieved_all("artists", artists.count()))
        response = ArtistResponseSerializer(artists, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_artist",
        tags=['Database Management'],
        summary="Create a New Artist",
        description="Adds a new artist entry to the database. A successful creation returns the newly created artist object with a 201 Created status code.",
        request=ArtistRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                ArtistResponseSerializer,
                name="ArtistCreated",
                description="The artist was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="ArtistCreateInvalidPayload",
                success=False,
                description="The request payload was invalid (e.g., missing a required field)."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ArtistResponseSerializer,
                name="ArtistCreateForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        """Handles POST requests to create a new artist.

        Args:
            request (Request):  The incoming HTTP request containing the data for
                                the new artist.

        Returns:
            Response:   A DRF Response with the newly created artist's data and a
                        201 Created status, or a 400 Bad Request on validation error.
        """
        self.log.debug(Messages.Post.create_one("artist", request.data))
        artist = ArtistRequestSerializer(data = request.data)
        
        if artist.is_valid():
            instance = artist.save()
            self.log.info(Messages.Post.created_one("artist", instance.id))
            return Response(
                data=ArtistResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
                )
        
        self.log.warning(Messages.Post.validation_failed("artist", artist.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(artist.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )