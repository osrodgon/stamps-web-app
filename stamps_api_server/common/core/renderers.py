from rest_framework.renderers import JSONRenderer

class StandardJSONRenderer(JSONRenderer):
    """
    Ensure all responses follow a standard format with dynamic messages.
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")
        request = renderer_context.get("request")

        # Default placeholders
        success = True
        message = "Request successful"
        errors = None

        if response is not None:
            status_code = response.status_code

            # 🔹 Handle errors
            if status_code >= 400:
                success = False
                message = "Request failed"
                errors = data
                data = None
            else:
                # 🔹 Dynamic success messages
                if request:
                    method = request.method.upper()
                    match method:
                        case "POST":
                            if status_code == 201:
                                message = "Created successfully"
                        case "PUT":
                            message = "Updated successfully"
                        case "PATCH":
                            message = "Partially updated successfully"
                        case "DELETE":
                            message = "Deleted successfully"
                        case "GET":
                            message = "Retrieved successfully"

        standard_data = {
            "success": success,
            "message": message,
            "data": data,
            "errors": errors,
        }

        return super().render(standard_data, accepted_media_type, renderer_context)
