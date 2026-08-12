from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        elif hasattr(exc, "messages"):
            exc = DRFValidationError(detail=exc.messages)
        else:
            exc = DRFValidationError(detail=exc.message)

    return exception_handler(exc, context)
