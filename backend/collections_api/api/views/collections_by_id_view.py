from functools import partial
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from common import api
from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.core.api_key_utils import ApiKeyUtils
from common.log.logger import Logger
from common.core.schemas import standardized_response
from collections_api.models import Collection
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from collections_api.api.serializers.collection_request_serializer import CollectionRequestSerializer

class CollectionsByIdView(Logger, APIView):
    """Manages API operations for a single Collection instance.

    This view handles the retrieval (GET), update (PUT), and deletion (DELETE)
    of a specific `Collection` object, identified by its primary key (`pk`)
    provided in the URL. Access is restricted to the owner of the collection.
    """
    serializer_class = CollectionResponseSerializer

    def __get_object(self, pk: int) -> Collection:
        """Retrieves a Collection instance by its primary key.

        Args:
            pk (int): The primary key of the collection to retrieve.

        Returns:
            Collection: The found collection instance, or None if it does not exist.
        """
        try:
            self.debug(Messages.Database.querying("collection", pk))
            return Collection.objects.get(pk=pk)
        except Collection.DoesNotExist:
            self.warning(Messages.Database.not_found("collection", pk))
            return None


    @extend_schema(
        operation_id="get_collection_by_id",
        tags=['Collection Management'],
        summary="Get Collection by ID",
        description="Retrieves a single collection entry by its unique ID. A 404 Not Found response is returned if the collection does not exist.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionResponseSerializer,
                name="CollectionRetrieved",
                description="The collection was retrieved successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionResponseSerializer,
                name="CollectionRetrieveForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionNotFound",
                success=False,
                description="The collection with the specified ID was not found."
            )
        }
    )
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve a single collection.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the collection to retrieve.

        Returns:
            Response:   A DRF Response object with the serialized collection
                        data and 200 OK status, or a 404 Not Found response.
        """
        self.debug(Messages.Get.retrieve_one("collection", pk))
        collection = self.__get_object(pk)
        
        if collection is None:
            message = Messages.Get.not_found("collection", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        response = CollectionResponseSerializer(collection)
        self.debug(Messages.Get.retrieved_one("collection", pk))
        return Response(data=response.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="update_collection",
        tags=['Collection Management'],
        summary="Update a Collection",
        description="Updates an existing collection entry identified by its ID. The request body must contain the updated collection data. A successful update returns the modified collection object.",
        request=CollectionRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionResponseSerializer,
                name="CollectionUpdated",
                description="The collection was updated successfully."
            ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CollectionUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionResponseSerializer,
                name="CollectionUpdateForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionUpdateNotFound",
                success=False,
                description="The collection with the specified ID was not found."
            )
        }
    )
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles PUT requests to update an existing collection.

        Args:
            request (Request): The incoming HTTP request containing update data.
            pk (int): The primary key of the collection to update.

        Returns:
            Response:   A DRF Response with updated data and 200 OK status,
                        a 404 if not found, or a 400 on validation error.
        """
        self.debug(Messages.Put.update_one("collection", pk, request.data))
        collection = self.__get_object(pk)
        if collection is None:
            message = Messages.Put.not_found("collection", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
                
        updated_collection = CollectionRequestSerializer(instance=collection, data=request.data, partial=False)

        if updated_collection.is_valid():
            instance = updated_collection.save()
            self.info(Messages.Put.updated_one("collection", pk))
            return Response(
                data=CollectionResponseSerializer(instance).data, 
                status=status.HTTP_200_OK
            )

        self.warning(Messages.Put.validation_failed("collection", pk, updated_collection.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(updated_collection.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        operation_id="delete_collection",
        tags=['Collection Management'],
        summary="Delete a Collection",
        description="Deletes a collection entry by its unique ID. A successful deletion returns a 204 No Content response.",
        responses={
            status.HTTP_204_NO_CONTENT: standardized_response(
                CollectionResponseSerializer,
                name="CollectionDeleted",
                success=True,
                description="The collection was deleted successfully."
            ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionResponseSerializer,
                name="CollectionDeleteForbidden",
                success=False,
                description="Permission denied."
            ),
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="CollectionDeleteNotFound",
                success=False,
                description="The collection with the specified ID was not found."
            )
        }
    )
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        """Handles DELETE requests to remove a collection.

        Args:
            request (Request): The incoming HTTP request.
            pk (int): The primary key of the collection to delete.

        Returns:
            Response:   A DRF Response with a success message and 200 OK status,
                        or a 404 Not Found response if the item does not exist.
        """
        self.debug(Messages.Delete.delete_one("collection", pk))
        collection = self.__get_object(pk)
        if collection is None:
            message = Messages.Delete.not_found("collection", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
            
        collection.delete()
        message = Messages.Delete.deleted_one("collection", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )
