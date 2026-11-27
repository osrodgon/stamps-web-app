from rest_framework import serializers

class GenericResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    errors = serializers.CharField()
    
class GenericResponse():
    def __init__(self, data= None, many=False):
        if isinstance(data, str):
            self.message = data
            self.errors = None
        elif isinstance(data, dict):
            self.message = data.get('message') or data.get('detail')
            if not self.message:
                self.message = data
            self.errors = data.get('error')
        else:
            self.message = data
            self.errors = None
        self.many = many
        
    @property
    def data(self):
        return GenericResponseSerializer(self).data
    
    @property
    def serializer(self):
        return GenericResponseSerializer(self)
    