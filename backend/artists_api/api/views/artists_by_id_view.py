from re import M
from common.api.messages import Messages
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from artists_api.models import Artist
from artists_api.api.serializers.artist_response_serializer import ArtistResponseSerializer
from artists_api.api.serializers.artist_request_serializer import ArtistRequestSerializer


class ArtistsByIdView(Logger, APIView):
    """Manages API operations for a single Artist instance.

    This view handles the retrieval (GET), update (PUT), and deletion (DELETE)
    of a specific `Artist` object, identified by its primary key (`pk`)
    provided in the URL.
    """
    serializer_class = ArtistResponseSerializer
    def __get_artist(self, pk: int) -> Artist:
        """Retrieves an Artist instance by its primary key.

        Args:
            pk (int): The primary key of the artist to retrieve.

        Returns:
            Artist: The found artist instance, or None if it does not exist.
        """
        try:
            self.log.debug(Messages.Database.querying("artist", pk))
            return Artist.objects.get(pk=pk)
        except Artist.DoesNotExist:
            self.log.warning(Messages.Database.not_found("artist", pk))
            return None
    
    @extend_schema(
        operation_id="retrieve_artist",
        tags=['Database Management'],
        summary="Retrieve an Artist by ID",
        description="Fetches the details of a specific artist entry by its unique identifier.",
        responses={
            200: standardized_response(
                ArtistResponseSerializer,
                name="ArtistRetrieved",
                description="The requested artist's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveArtistNotFound",
                success=False,
                description="No artist was found for the provided ID."
                ),
            403: standardized_response(
                ArtistResponseSerializer,
                name="RetrieveArtistForbidden",
                success=False,
                description="Permission denied."
                )   
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve a single artist.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the artist to retrieve.

        Returns:
            Response:   A DRF Response object with the serialized artist
                        data and 200 OK status, or a 404 Not Found response.
        """
        self.log.debug(Messages.Get.retrieve_one("artist", pk))
        artist = self.__get_artist(pk)
        
        if artist is None:
            message = Messages.Get.not_found("artist", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = ArtistResponseSerializer(artist)
        self.log.info(Messages.Get.retrieved_one("artist", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_artist",
        tags=['Database Management'],
        summary="Update an Artist",
        description="Updates an existing artist entry identified by its ID. A complete payload with all required fields is expected.",
        request=ArtistRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                ArtistResponseSerializer,
                name="ArtistUpdated",
                description="The artist was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="ArtistUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ArtistResponseSerializer,
                name="ArtistUpdateForbidden",
                success=False,
                description="Permission denied."
                ),    
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="ArtistUpdateNotFound",
                success=False,
                description="The artist with the specified ID was not found."
                )
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles PUT requests to update an existing artist.

        Args:
            request (Request): The incoming HTTP request containing update data.
            pk (int): The primary key of the artist to update.

        Returns:
            Response:   A DRF Response with updated data and 200 OK status,
                        a 404 if not found, or a 400 on validation error.
        """
        self.log.debug(Messages.Put.update_one("artist", pk, request.data))
        artist = self.__get_artist(pk)
        if artist is None:
            message = Messages.Put.not_found("artist", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        updated_artist = ArtistRequestSerializer(data=request.data, instance=artist, partial=False)
        if updated_artist.is_valid():
            instance = updated_artist.save()
            self.log.info(Messages.Put.updated_one("artist", instance.id))
            return Response(
                data=ArtistResponseSerializer(instance).data,
                status=status.HTTP_200_OK
                )
        
        self.log.warning(Messages.Put.validation_failed("artist", pk, updated_artist.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_artist.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        operation_id="delete_artist",
        tags=['Database Management'],
        summary="Delete an Artist",
        description="Deletes an artist entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="ArtistDeleted",
                success=True,
                description="The artist was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                ArtistResponseSerializer,
                name="ArtistDeleteForbidden",
                success=False,
                description="Permission denied."
                ),   
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="ArtistDeleteNotFound",
                success=False,
                description="The artist with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles DELETE requests to remove an artist.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the artist to delete.

        Returns:
            Response:   A DRF Response with a success message and 200 OK status,
                        or a 404 Not Found response if the item does not exist.
        """
        self.log.debug(Messages.Delete.delete_one("artist", pk))
        artist = self.__get_artist(pk)
        if artist is None:
            message = Messages.Delete.not_found("artist", pk)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        artist.delete()
        message = Messages.Delete.deleted_one("artist", pk)
        self.log.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )