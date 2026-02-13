from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    errors = serializers.CharField()
    
class GenericResponse():
    def __init__(self, data= None, many=False):
        if isinstance(data, str):
            self.message = data
            self.errors = None
        else:
            self.message = data.get('message', str(data)) or data.get('detail', str(data))
            self.errors = data.get('error', None)
        self.many = many
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    
    @property
    def serializer(self):
        return GenericResponseSerializer(self)
    