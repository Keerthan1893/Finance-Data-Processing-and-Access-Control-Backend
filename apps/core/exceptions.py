from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {"success": False, "message": "An unexpected server error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data

    
    if isinstance(data, dict) and list(data.keys()) == ["detail"]:
        return Response(
            {"success": False, "message": str(data["detail"])},
            status=response.status_code,
        )

    
    return Response(
        {
            "success": False,
            "message": "Validation failed. Please check the provided data.",
            "errors": data,
        },
        status=response.status_code,
    )
