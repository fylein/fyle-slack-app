from fyle_slack_app.libs.assertions import assert_auth, assert_found, assert_good, assert_true, assert_valid
from fyle_slack_app.libs.assertions import InvalidUsage
import pytest

class TestAssertions:

    def test_auth(self):
        with pytest.raises(InvalidUsage):
            assert_auth(False, message = "Unauthorized")
        assert_auth(True, message = "Unauthorized")

    def test_found(self):
        with pytest.raises(InvalidUsage):
            assert_found(None, message = "Not Found")
        assert_found('dummy_string', message = "Found")

    def test_good(self):
        with pytest.raises(InvalidUsage):
            assert_good(False, message = "Not Good")
        assert_good(True, message = "Good")

    def test_true(self):
        with pytest.raises(InvalidUsage):
            assert_true(False, message = "Not True")
        assert_true(True, message = "True")

    def test_valid(self):
        with pytest.raises(InvalidUsage):
            assert_valid(False, message = "Not Valid")
        assert_valid(True, message = "Valid")
