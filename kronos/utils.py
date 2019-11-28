

def serializable_dict(d):

    def _safe_value(value):
        from decimal import Decimal
        from datetime import date, datetime, time

        if isinstance(value, Decimal):
            _v = str(value)
        elif isinstance(value, (datetime, date, time)):
            _v = value.isoformat()
        elif isinstance(value, dict):
            _v = serializable_dict(value)
        elif isinstance(value, (list, set, tuple)):
            _v = [_safe_value(e) for e in value]
        else:
            _v = value

        return _v

    _d = {}
    for k, v in d.items():
        _d[k] = _safe_value(v)

    return _d
