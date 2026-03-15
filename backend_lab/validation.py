"""Small shared helpers: reject ambiguous inputs at the API boundary."""

from flask import abort, request


def json_object():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400, description="The JSON body must be an object.")
    return data


def query_int(name, default, maximum):
    value = request.args.get(name)
    if value is None:
        return default
    if not value.isascii() or not value.isdigit():
        abort(400, description=f"{name} must be a positive integer.")
    # Bound the string before int() to avoid huge numeric input.
    if len(value) > 9 or not 1 <= int(value) <= maximum:
        abort(400, description=f"{name} must be between 1 and {maximum}.")
    return int(value)


def query_fields(allowed):
    if set(request.args) - set(allowed):
        abort(400, description="Unknown query parameter.")
    if any(len(request.args.getlist(key)) != 1 for key in request.args):
        abort(400, description="Query parameters must not be repeated.")
