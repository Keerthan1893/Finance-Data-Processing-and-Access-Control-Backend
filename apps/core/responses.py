from rest_framework.response import Response


def success_response(data=None, message="Success", status=200, **kwargs):
    """Returns a consistent success response structure."""
    is_success = 200 <= status < 300
    payload = {"success": is_success, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return Response(payload, status=status)


def error_response(message="Error", errors=None, status=400, **kwargs):
    """Returns a consistent error response structure."""
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    payload.update(kwargs)
    return Response(payload, status=status)
