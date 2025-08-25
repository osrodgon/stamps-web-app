from drf_yasg.generators import OpenAPISchemaGenerator

class CustomOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        """_summary_

        Args:
            request (_type_, optional): _description_. Defaults to None.
            public (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """
        swagger = super().get_schema(request, public)
        swagger.tags = [
            {
                "name": "Years",
                "description": "List of all APIs available for year operations."
            }
        ]
        return swagger