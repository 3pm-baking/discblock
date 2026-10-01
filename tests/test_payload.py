import pytest

from discblock import ClickPayload, decode, encode


class TestEncodeDecode:
    def test_round_trip(self):
        custom_id = encode("west_asheville")
        assert decode(custom_id) == ClickPayload(value="west_asheville")

    def test_round_trip_with_action(self):
        action = {"op": "print", "file": "tally.pdf"}
        custom_id = encode("tally", action)
        assert decode(custom_id) == ClickPayload(value="tally", action=action)

    def test_versioned_prefix(self):
        assert encode("x").startswith("db1|")

    def test_over_100_chars_rejected(self):
        with pytest.raises(ValueError, match="too long"):
            encode("v" * 200)

    def test_unicode_values_survive(self):
        custom_id = encode("käsebrötchen")
        assert decode(custom_id).value == "käsebrötchen"


class TestDecodeErrors:
    def test_foreign_custom_id_rejected(self):
        with pytest.raises(ValueError, match="not a discblock"):
            decode("somethingelse|abc")

    def test_garbage_body_rejected(self):
        with pytest.raises(ValueError, match="malformed"):
            decode("db1|!!!")

    def test_missing_value_rejected(self):
        import base64

        body = base64.urlsafe_b64encode(b'{"a":null}').decode().rstrip("=")
        with pytest.raises(ValueError, match="missing 'v'"):
            decode(f"db1|{body}")
