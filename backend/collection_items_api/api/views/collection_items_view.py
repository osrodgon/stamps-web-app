from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.core.authentication import APIKeyAuthentication
from common.log.logger import Logger
from common.core.schemas import standardized_response
from collection_items_api.models import CollectionItem
from collection_items_api.api.serializers.collection_items_response_serializer import CollectionItemsResponseSerializer
from collection_items_api.api.serializers.collection_items_request_serializer import CollectionItemsRequestSerializer


class CollectionItemsView(Logger, APIView):
    serializer_class = CollectionItemsResponseSerializer
    
    @extend_schema(
        operation_id="list_collection_items",
        tags=['Collection Items'],
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
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("collection items"))
        collection_items = CollectionItem.objects.all()
        self.debug(Messages.Get.retrieved_all("collection items", len(collection_items)))
        response = CollectionItemsResponseSerializer(collection_items, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_collection_item",
        tags=['Collection Items'],
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
                description="Permission denied. You're likely missing X-API-Key header."
            )
        }
    )
    def post(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Post.create_one("collection item", request.data))
        collection_item = CollectionItemsRequestSerializer(data = request.data)
        
        if collection_item.is_valid():
            instance = collection_item.save()
            self.info(Messages.Post.created_one("collection item", instance.id))
            return Response(
                data=CollectionItemsResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.warning(Messages.Post.validation_failed("collection item", collection_item.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(collection_item.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )