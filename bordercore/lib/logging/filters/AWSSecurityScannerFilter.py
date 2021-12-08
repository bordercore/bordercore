import logging


class AWSSecurityScannerFilter(logging.Filter):
    def filter(self, record):

        if record.request.META.get("HTTP_USER_AGENT", None) == "AWS Security Scanner":
            return False

        return True
