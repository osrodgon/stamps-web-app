import re
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from common.api.messages import Messages

class StandardJSONRenderer(JSONRenderer):
    def errors_to_list(self, errors):
        # Define a regular expression to find all key-value pairs
        # This pattern looks for a field name, a message, and a code
        pattern = r"'([^']+)': ErrorDetail\(string='([^']+)', code='([^']+)'\)"

        # Find all matches in the string
        matches = re.findall(pattern, errors)
        
        if not matches:
            pattern = r"'([^']+)': \[ErrorDetail\(string='([^']+)', code='([^']+)'\)\]"
            matches = re.findall(pattern, errors)
        
        # Create an empty list to store the results
        errors_list = []

        # Iterate over each match and format it into a dictionary
        for field_name, error_message, error_code in matches:
            error_dict = {
                "field": field_name,
                "message": error_message,
                "code": error_code
            }
            errors_list.append(error_dict)
            
        if not errors_list:
            errors_list.append(
                {
                    "field": None,
                    "message": errors,
                    "code": Messages.Code.other()
                }
            )

        return errors_list
        
    """
    Ensure all responses follow a standard format with dynamic messages.
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")
        request = renderer_context.get("request")

        # Default placeholders
        success = True
        message = Messages.success()
        errors = None
        data =data

        if response is not None:
            status_code = response.status_code
            
            # 🔹 Handle errors
            if status_code >= status.HTTP_400_BAD_REQUEST:
                if (
                    status_code == status.HTTP_403_FORBIDDEN or
                    status_code == status.HTTP_500_INTERNAL_SERVER_ERROR or
                    status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                ):
                    success = data['success']
                    message = data['message']
                    errors = self.errors_to_list(f"'internal_server_error': {data['errors']}")
                    data = data['data']
                else:
                    success = False
                    message = Messages.failed()
                    errors = self.errors_to_list(data['message'])
                    data = None
            else:
                # 🔹 Dynamic success messages
                if request:
                    method = request.method.upper()
                    match method:
                        case "POST":
                            if status_code == status.HTTP_201_CREATED:
                                message = Messages.created_successfully()
                        case "PUT":
                            message = Messages.updated_successfully()
                        case "PATCH":
                            message = Messages.partially_updated_successfully()
                        case "DELETE":
                            message = Messages.deleted_successfully()
                        case "GET":
                            message = Messages.retrieved_successfully()

        standard_data = {
            "success": success,
            "message": message,
            "errors": errors,
            "data": data
        }

        return super().render(standard_data, accepted_media_type, renderer_context)
