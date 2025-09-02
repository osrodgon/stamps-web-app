from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    
class GenericResponse():
    def __init__(self, detail=None, many=False):
        self.detail = detail
        self.many = many
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    
    @property
    def serializer(self):
        return GenericResponseSerializer(self)
    