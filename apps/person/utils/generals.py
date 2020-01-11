import uuid

def random_string():
    """ Global verification code """
    length = 6
    code = uuid.uuid4().hex
    code = code.upper()[0:length]
    return code
