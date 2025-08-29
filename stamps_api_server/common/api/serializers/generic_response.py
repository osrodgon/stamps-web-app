from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    information = serializers.CharField()
    
class GenericResponse():
    def __init__(self, information=None, many=False):
        self.information = information
        self.many = many
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    
    @property
    def serializer(self):
        return GenericResponseSerializer(self)
    