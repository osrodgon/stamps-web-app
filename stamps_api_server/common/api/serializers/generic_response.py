from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    
class GenericResponse():
    def __init__(self, message= None, many=False):
        self.message = message
        self.many = many
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    
    @property
    def serializer(self):
        return GenericResponseSerializer(self)
    