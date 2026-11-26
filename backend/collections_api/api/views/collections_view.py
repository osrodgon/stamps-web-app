from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.log.logger import Logger
from common.core.current_user import CurrentUser
from common.core.schemas import standardized_response
from collections_api.services.collection_overview_service import CollectionOverviewService
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from collections_api.api.serializers.collection_overview_serializer import CollectionOverviewSerializer
from collections_api.api.serializers.collection_request_serializer import CollectionRequestSerializer


class CollectionsView(Logger, APIView):
    """Manages bulk API operations for Collection instances.

    This view handles the retrieval of the caller's collections (GET) and the
    creation of a new one (POST). The user comes from the JWT the login returns
    (plan step A1): the view never returns another user's rows and never takes the
    owner from the request body or from the API key.
    """
    serializer_class = CollectionResponseSerializer
    
    @extend_schema(
        operation_id="list_collections",
        tags=['Collection Management'],
        summary="List My Collections",
        description="Retrieves the collections that belong to the user of the JWT, with their counters (series, stamps, total) and up to twelve cover candidates. Another user's collections are never returned.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionOverviewSerializer, 
                name="CollectionsRetrieved",
                description="A list of collections was successfully retrieved.",
                many=True
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionResponseSerializer,
                name="CollectionsRetrieveForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Handles GET requests to retrieve the caller's collections.

        Args:
            request (Request): The incoming HTTP request, with the user's JWT.

        Returns:
            Response: A DRF Response object with one overview row per
                collection (counters and covers), ordered by name.
        """
        self.log.debug(Messages.Get.retrieve_all("collections"))
        user = CurrentUser(request).get()

        overview = CollectionOverviewService().for_user(user)
        self.log.debug(Messages.Get.retrieved_all("collections", len(overview)))
        response = CollectionOverviewSerializer(overview, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_collection",
        tags=['Collection Management'],
        summary="Create a New Collection",
        description="Adds a collection owned by the user of the JWT. The request body carries the name; a `user` in the body is ignored.",
        request=CollectionRequestSerializer,
        responses={
            status.HTTP_201_CREATED: standardized_response(
                CollectionResponseSerializer,
                name="CollectionCreated",
                description="The collection was created successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="CollectionCreateInvalidPayload",
                success=False,
                description="The request payload was invalid.",
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                CollectionResponseSerializer,
                name="CollectionCreateForbidden",
                success=False,
                description="Permission denied."
            )
        }
    )
    
    def post(self, request: Request, *args, **kwargs) -> Response:
        """Handles POST requests to create a collection for the caller.

        Args:
            request (Request): The incoming HTTP request with the name of the
                collection and the user's JWT.

        Returns:
            Response: A DRF Response with the new collection and 201, or a 400
                when the payload is invalid.
        """
        self.log.debug(Messages.Post.create_one("collection", request.data))
        user = CurrentUser(request).get()
        collection = CollectionRequestSerializer(data=request.data)

        if collection.is_valid():
            instance = collection.save(user=user)
            self.log.info(Messages.Post.created_one("collection", instance.id))
            return Response(
                data=CollectionResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.log.warning(Messages.Post.validation_failed("collection", collection.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(collection.errors)).data,
            status=status.HTTP_400_BAD_REQUEST
        )