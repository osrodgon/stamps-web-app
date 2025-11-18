from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.schemas import standardized_response
from collection_items_api.models import CollectionItem
from collection_items_api.api.serializers.collection_items_response_serializer import CollectionItemsResponseSerializer
from collection_items_api.api.serializers.collection_items_request_serializer import CollectionItemsRequestSerializer


class CollectionItemsView(Logger, APIView):
    """Manages bulk API operations for CollectionItem instances.

    This view handles the retrieval of all collection items (GET) and the
    creation of a new collection item (POST).

    It uses `CollectionItemsRequestSerializer` for validating incoming data on
    creation and `CollectionItemsResponseSerializer` for formatting the outgoing
    response for both GET and POST requests.
    """
    serializer_class = CollectionItemsResponseSerializer
    
    @extend_schema(
        operation_id="list_collection_items",
        tags=['Collection Management'],
        summary="List All Collection Items",
        description="Retrieves a list of all collection item entries currently stored in the database. The response will contain an array of collection item objects.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionItemsResponseSerializer, 
                name="CollectionItemsRetrieved",
                description="A list of collection items was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemsRetrieveForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve all collection items.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response:   A DRF Response object containing a list of all serialized
                        collection item objects and a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("collection items"))
        collection_items = CollectionItem.objects.all()
        self.log.debug(Messages.Get.retrieved_all("collection items", len(collection_items)))
        response = CollectionItemsResponseSerializer(collection_items, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_collection_item",
        tags=['Collection Management'],
        summary="Create a New Collection Item",
        description="Adds a new collection item entry to the database. The request body must contain the collection item data. A successful creation returns the newly created collection item object with a 201 status code.",
        request=CollectionItemsRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemCreated",
                description="The collection item was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CollectionItemCreateInvalidPayload",
                success=False,
                description="The request payload was invalid.",
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionItemsResponseSerializer,
                name="CollectionItemCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Handles POST requests to create a new collection item.

        Args:
            request (Request):  The incoming HTTP request containing the data for
                                the new collection item.

        Returns:
            Response:   A DRF Response with the newly created item's data and a
                        201 Created status, or a 400 Bad Request on validation error.
        """
        self.log.debug(Messages.Post.create_one("collection item", request.data))
        collection_item = CollectionItemsRequestSerializer(data = request.data)
        
        if collection_item.is_valid():
            instance = collection_item.save()
            self.log.info(Messages.Post.created_one("collection item", instance.id))
            return Response(
                data=CollectionItemsResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.log.warning(Messages.Post.validation_failed("collection item", collection_item.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(collection_item.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )