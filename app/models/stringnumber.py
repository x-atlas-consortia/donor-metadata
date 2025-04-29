def stringisnumber(s:str) -> bool:
    """
    Checks whether a string represents a number.
    :param s: the string to check
    :return: true if the string can represent a number; false otherwise.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def stringisintegerorfloat(s:str) ->str:
    """
    Returns whether a string is an integer or float.
    :param: str: number to check
    :return: "float","integer", or "not a number"
    """

    if stringisnumber(s):
        if s.isdigit():
            return "integer"
        else:
            return "float"

    return "not a number"

