import re
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from common.api.messages import Messages

class StandardJSONRenderer(JSONRenderer):
    def errors_to_list(self, errors):
        if not errors:
            return []

        errors_list = []

        # Try to convert to dict
        if isinstance(errors, str):
            # Define a regular expression to find all key-value pairs
            # This pattern looks for a field name, a message, and a code
            pattern = r"'([^']+)': ErrorDetail\(string='([^']+)', code='([^']+)'\)"

            # Find all matches in the string
            matches = re.findall(pattern, errors)
            
            if not matches:
                pattern = r"'([^']+)': \[ErrorDetail\(string='([^']+)', code='([^']+)'\)\]"
                matches = re.findall(pattern, errors)

            # Create an empty list to store the results
            errors_dict = {}
            
            for match in matches:
                field, message, code = match
                # item = type('ErrorItem', (object,), {'message': message, 'code': code})()
                if field not in errors_dict:
                    errors_dict[field] = []
                errors_dict[field].append(
                    {
                        "message": message,
                        "code": code
                    }
                )
            
            if errors_dict:
                errors = errors_dict

        if isinstance(errors, dict):
                for field, value in errors.items():
                    if isinstance(value, list):
                        for item in value:
                            errors_list.append({
                                "field": field,
                                "message": item.get('message', Messages.failed()),
                                "code": item.get('code', Messages.Code.other())
                            })
                    else:
                        errors_list.append({
                            "field": field,
                            "message": str(value),
                            "code": getattr(value, 'code', Messages.Code.other())
                        })
        elif isinstance(errors, list):
            for item in errors:
                errors_list.append({
                    "field": None,
                    "message": str(item),
                    "code": getattr(item, 'code', Messages.Code.other())
                })
        else:
            errors_list.append(
                {
                    "field": None,
                    "message": str(errors),
                    "code": getattr(errors, 'code', Messages.Code.other())
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
            
            # Handle errors
            if status_code >= status.HTTP_400_BAD_REQUEST:
                if (
                    status_code == status.HTTP_403_FORBIDDEN or
                    status_code == status.HTTP_422_UNPROCESSABLE_ENTITY or
                    status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                ):
                    try:
                        success = data['success']
                    except KeyError:
                        success = False
                    try:
                        message = data['message']
                        if not message:
                            message = Messages.failed()
                    except KeyError:
                        message = Messages.failed()
                    try:
                        errors = self.errors_to_list(data['errors'])
                    except KeyError:
                        errors = None
                    try:
                        data = data['data']
                    except KeyError:
                        data = None
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
