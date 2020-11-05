class QueryFormatError(Exception):
    """Invalid Query Format."""

# Suppressing Context
# Mantener compatibilidad syntaxis Python 3 (raise Exception from Cause)
def raise_from_cause(Exception,Cause):
    _exception = Exception
    _exception.__cause__ = Cause
    return _exception 