from datetime import datetime, timedelta, timezone
import uuid
import jwt

from _backend.settings import JWT_ALGORITHM, JWT_SECRET
from common.log.logger import Logger
from users_api.models import UserCollection, UserToken


class JwtToken(Logger):
    def validate(self, token: str):
        self.debug("Validating JWT token...")
        try:
            jwt_payload = jwt.decode(
                token,
                key=JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )
            try:
                UserToken.objects.get(user=jwt_payload['user_id'], jti=jwt_payload['jti'])
            except UserToken.DoesNotExist:
                self.error("The token is not associated with a valid user.")
                return None
                
            self.debug("JWT token validated.")
            return jwt_payload
    
        except jwt.ExpiredSignatureError:
            self.error("JWT token has expired.")
            return None
        except jwt.InvalidTokenError as e:
            self.error(f"JWT token validation failed: {e}")
            return None
    
    def create(self, user: UserCollection) -> str:
        self.debug("Creating JWT token...")
        current_time_utc = datetime.now(timezone.utc)
        
        jwt_payload = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'jti': str(uuid.uuid4()),
            'exp': current_time_utc + timedelta(days=1),
            'iat': current_time_utc
        }
        try:
            token = jwt.encode(
                jwt_payload,
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            )
        except TypeError:
            self.error("JWT token creation failed: payload is invalid.")
            return None
        except jwt.InvalidAlgorithmError:
            self.error("JWT token creation failed: invalid algorithm.")
            return None
        except jwt.InvalidTokenError:
            self.error("JWT token creation failed: invalid token.")
            return None
        
        self.debug("JWT token created.")
        UserToken.objects.update_or_create(user=user, defaults={'jti': jwt_payload['jti']})    
        return {
            'token': token,
            'payload': jwt_payload
        }