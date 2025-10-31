from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from common.api.messages import Messages
from common.api.serializers.generic_response import GenericResponseSerializer, GenericResponse
from common.core.api_key_utils import ApiKeyUtils
from common.log.logger import Logger
from common.core.schemas import standardized_response
from collections_api.models import Collection
from collections_api.api.serializers.collection_response_serializer import CollectionResponseSerializer
from collections_api.api.serializers.collection_request_serializer import CollectionRequestSerializer
from users_api.models import UserCollection


class CollectionsView(Logger, APIView):
    serializer_class = CollectionResponseSerializer
    api_key = ApiKeyUtils()
    
    @extend_schema(
        operation_id="list_collections",
        tags=['Collection Management'],
        summary="List All Collections",
        parameters=[
            OpenApiParameter(
                name='username',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter collections by username.",
                required=False
            )
        ],
        description="Retrieves a list of all collection entries currently stored in the database. The response will contain an array of collection objects.",
        responses={
            status.HTTP_200_OK: standardized_response(
                CollectionResponseSerializer, 
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
    def get(self, request:Request, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_all("collections"))
        username = request.query_params.get('username')

        collections = Collection.objects.all()
        self.debug(Messages.Get.retrieved_all("collections", len(collections)))
        response = CollectionResponseSerializer(collections, many=True)
        
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="create_collection",
        tags=['Collection Management'],
        summary="Create a New Collection",
        description="Adds a new collection entry to the database. The request body must contain the collection data. A successful creation returns the newly created collection object with a 201 status code.",
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
    def post(self, request:Request, *args, **kwargs) -> Response:
        password_hash = request.META.get('HTTP_X_API_KEY')
        user = self.__get_user(password_hash)
        self.debug(Messages.Post.create_one("collection", request.data))
        collection = CollectionRequestSerializer(data = request.data)
        
        if user is None:
            message = Messages.Database.unknow_user()
            self.warning(message) 
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if collection.is_valid():
            instance = collection.save(user=user)
            self.info(Messages.Post.created_one("collection", instance.id))
            return Response(
                data=CollectionResponseSerializer(instance).data, 
                status=status.HTTP_201_CREATED
            )
        
        self.warning(Messages.Post.validation_failed("collection", collection.errors))
        return Response(
            data=GenericResponseSerializer(GenericResponse(collection.errors)).data, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    def __get_user(self, password_hash):
        try:
            return UserCollection.objects.get(password_hash=password_hash)
        except UserCollection.DoesNotExist:
            return None

