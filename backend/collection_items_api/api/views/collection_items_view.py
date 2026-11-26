from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.current_user import CurrentUser
from common.core.schemas import standardized_response
from collection_items_api.models import CollectionItem
from collections_api.models import Collection
from collection_items_api.api.serializers.collection_items_response_serializer import CollectionItemsResponseSerializer
from collection_items_api.api.serializers.collection_items_request_serializer import CollectionItemsRequestSerializer


class CollectionItemsView(Logger, APIView):
    """Manages bulk API operations for CollectionItem instances.

    This view handles the retrieval of all collection items (GET) and the
    creation of a new collection item (POST).

    It uses `CollectionItemsRequestSerializer` for validating incoming data on
    creation and `CollectionItemsResponseSerializer` for formatting the outgoing
    response for both GET and POST requests.

    Everything is scoped to the user of the JWT (plan step A1): the list never
    returns another user's items, and an item can only be added to a collection
    that belongs to the caller.
    """
    serializer_class = CollectionItemsResponseSerializer
    
    @extend_schema(
        operation_id="list_collection_items",
        tags=['Collection Management'],
        summary="List My Collection Items",
        description="Retrieves the items of the collections that belong to the user of the JWT.",
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
        """Handles GET requests to retrieve the caller's collection items.

        Args:
            request (Request): The incoming HTTP request, with the user's JWT.

        Returns:
            Response:   A DRF Response object containing a list of the serialized
                        collection items of that user and a 200 OK status.
        """
        self.log.debug(Messages.Get.retrieve_all("collection items"))
        user = CurrentUser(request).get()
        collection_items = CollectionItem.objects.filter(collection__user=user)

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
        description="Adds an item to one of the caller's collections. A `collection` that belongs to another user is reported as not found.",
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
        user = CurrentUser(request).get()

        # Ownership comes before validation: a foreign collection must answer 404
        # even when the pair it holds would fail the unique check, which would
        # otherwise tell the caller that somebody has that stamp there.
        collection_id = request.data.get("collection")
        if not self.__owns_collection(collection_id, user):
            message = Messages.Database.not_found("collection", collection_id)
            self.log.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
            )

        collection_item = CollectionItemsRequestSerializer(data=request.data)

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

    @staticmethod
    def __owns_collection(collection_id, user) -> bool:
        """True when the collection is the caller's, or when the id is not an id.

        A missing id is left to the serializer, which answers 400; a value that is
        not a number also goes there instead of becoming a 404 for the wrong
        reason.
        """
        if collection_id in (None, ""):
            return True

        try:
            return Collection.objects.filter(pk=collection_id, user=user).exists()
        except (TypeError, ValueError):
            return True