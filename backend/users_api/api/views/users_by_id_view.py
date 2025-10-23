from common.api.messages import Messages
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import make_password

from common.log.logger import Logger
from common.api.serializers.generic_response import GenericResponse, GenericResponseSerializer
from common.core.schemas import standardized_response
from users_api.models import UserCollection
from users_api.api.serializers.user_response_serializer import UserResponseSerializer
from users_api.api.serializers.user_request_serializer import UserRequestSerializer


class UsersByIdView(Logger, APIView):
    serializer_class = UserResponseSerializer
    
    def __get_user(self, pk: int) -> UserCollection:
        try:
            self.debug(Messages.Database.querying("collection user", pk))
            return UserCollection.objects.get(pk=pk)
        except UserCollection.DoesNotExist:
            self.debug(Messages.Database.not_found("collection user", pk))
            return None
    
    @extend_schema(
        operation_id="retrieve_user",
        tags=['Collection Users'],
        summary="Retrieve a Collection User by ID",
        description="Fetches the details of a specific collection user entry by its unique identifier.",
        responses={
            200: standardized_response(
                UserResponseSerializer,
                name="UserRetrieved",
                description="The requested collection user's data was retrieved successfully."
                ),
            404: standardized_response(
                GenericResponseSerializer,
                name="RetrieveUserNotFound",
                success=False,
                description="No collection user was found for the provided ID."
                ),
            403: standardized_response(
                UserResponseSerializer,
                name="RetrieveUserForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                )   
        }
    )    
    def get(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Get.retrieve_one("collection user", pk))
        user = self.__get_user(pk)
        
        if user is None:
            message = Messages.Get.not_found("collection user", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        response = UserResponseSerializer(user)
        self.info(Messages.Get.retrieved_one("collection user", pk))
        return Response(
            data=response.data, 
            status=status.HTTP_200_OK
            )
    
    @extend_schema(
        operation_id="update_user",
        tags=['Collection Users'],
        summary="Update a Collection User",
        description="Updates an existing collection user entry identified by its ID. A complete payload with all required fields is expected.",
        request=UserRequestSerializer,
        responses={
            status.HTTP_200_OK: standardized_response(
                UserResponseSerializer,
                name="UserUpdated",
                description="The collection user was updated successfully."
                ),
            status.HTTP_400_BAD_REQUEST: standardized_response(
                GenericResponseSerializer,
                name="UserUpdateInvalidPayload",
                success=False,
                description="The request payload was invalid."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                UserResponseSerializer,
                name="UserUpdateForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                ),    
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="UserUpdateNotFound",
                success=False,
                description="The collection user with the specified ID was not found."
                )
        }
    )    
    def put(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Put.update_one("collection user", pk, request.data))
        user = self.__get_user(pk)
        if user is None:
            message = Messages.Put.not_found("collection user", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = UserRequestSerializer(data=request.data, instance=user, partial=False)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            if 'password' in validated_data:
                validated_data['password_hash'] = make_password(validated_data.pop('password'))
            
            for attr, value in validated_data.items():
                setattr(user, attr, value)
            user.save()

            self.info(Messages.Put.updated_one("collection user", user.id))
            return Response(data=UserResponseSerializer(user).data, status=status.HTTP_200_OK)
        
        self.warning(Messages.Put.validation_failed("collection user", pk, serializer.errors))
        return Response(data=GenericResponseSerializer(GenericResponse(serializer.errors)).data, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        operation_id="delete_user",
        tags=['Collection Users'],
        summary="Delete a Collection User",
        description="Deletes a collection user entry from the database using its ID.",
        responses={
            status.HTTP_200_OK: standardized_response(
                GenericResponseSerializer,
                name="UserDeleted",
                success=True,
                description="The collection user was deleted successfully."
                ),
            status.HTTP_403_FORBIDDEN: standardized_response(
                UserResponseSerializer,
                name="UserDeleteForbidden",
                success=False,
                description="Permission denied. You're likely missing X-API-Key header."
                ),   
            status.HTTP_404_NOT_FOUND: standardized_response(
                GenericResponseSerializer,
                name="UserDeleteNotFound",
                success=False,
                description="The collection user with the specified ID was not found."
                )
        }
    )    
    def delete(self, request: Request, pk: int, *args, **kwargs) -> Response:
        self.debug(Messages.Delete.delete_one("collection user", pk))
        user = self.__get_user(pk)
        if user is None:
            message = Messages.Delete.not_found("collection user", pk)
            self.warning(message)
            return Response(
                data=GenericResponseSerializer(GenericResponse(message)).data,
                status=status.HTTP_404_NOT_FOUND
                )
        
        user.delete()
        message = Messages.Delete.deleted_one("collection user", pk)
        self.info(message)
        return Response(
            data=GenericResponseSerializer(GenericResponse(message)).data,
            status=status.HTTP_200_OK
            )