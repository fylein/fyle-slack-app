class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        self.payload = payload

        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        res = dict(self.payload or ())
        res['message'] = self.message
        return res


def assert_true(condition, message='Forbidden', status_code=403):
    if condition is not True:
        raise InvalidUsage(message, status_code=status_code)


def assert_found(instance, message='Not Found', status_code=404):
    if instance is None:
        raise InvalidUsage(message, status_code=status_code)


def assert_valid(condition, message='Bad Request'):
    assert_true(condition, message, status_code=400)


def assert_good(condition, message='Something went wrong'):
    assert_true(condition, message, status_code=500)


def assert_auth(condition, message='Unauthorized'):
    assert_true(condition, message, status_code=401)
