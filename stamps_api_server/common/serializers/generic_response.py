from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    
class GenericResponse():
    def __init__(self, message=None):
        self.message = message
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    
    @property
    def serializer(self):
        return GenericResponseSerializer(self)
    