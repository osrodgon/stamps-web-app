from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    
class GenericResponse():
    def __init__(self, message):
        self.message = message
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    