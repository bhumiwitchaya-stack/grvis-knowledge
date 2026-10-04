import socket
import unittest
from email.message import Message
from urllib.error import HTTPError
from unittest.mock import Mock
from unittest.mock import patch

from grvis_safe_web_reader.core import (
    MAX_RESPONSE_BYTES,
    SafetyError,
    canonical_hostname,
    fetch_public_text,
    validate_url,
)


def public_dns(_host, _port, *, type):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


def private_dns(_host, _port, *, type):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]


class UrlPolicyTests(unittest.TestCase):
    def test_accepts_exact_allowlisted_public_https_host(self):
        with patch("socket.getaddrinfo", public_dns):
            self.assertEqual(validate_url("https://example.com/page", {"example.com"}), "https://example.com/page")

    def test_rejects_unsafe_or_unapproved_urls(self):
        cases = [
            ("file:///etc/passwd", {"example.com"}),
            ("https://user:pass@example.com/", {"example.com"}),
            ("https://example.com.attacker.test/", {"example.com"}),
            ("https://example.com:8443/", {"example.com"}),
            ("http://example.com:443/", {"example.com"}),
            ("https://127.0.0.1/", {"127.0.0.1"}),
        ]
        with patch("socket.getaddrinfo", public_dns):
            for url, domains in cases:
                with self.subTest(url=url), self.assertRaises(SafetyError):
                    validate_url(url, domains)

    def test_rejects_non_public_dns_answer(self):
        with patch("socket.getaddrinfo", private_dns):
            with self.assertRaisesRegex(SafetyError, "non-public"):
                validate_url("https://example.com/", {"example.com"})

    def test_normalizes_idna_and_rejects_wildcards(self):
        self.assertEqual(canonical_hostname("BÜCHER.example."), "xn--bcher-kva.example")
        with self.assertRaises(SafetyError):
            canonical_hostname("*.example.com")


class FetchTests(unittest.TestCase):
    def response(self, body, content_type="text/html; charset=utf-8"):
        response = Mock()
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = content_type
        response.read.return_value = body
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    def test_extracts_html_as_untrusted_text_and_disables_proxy(self):
        response = self.response(b"<html><h1>Public</h1><script>secret()</script></html>")
        opener = Mock()
        opener.open.return_value = response
        with patch("socket.getaddrinfo", public_dns), patch(
            "grvis_safe_web_reader.core.build_opener", return_value=opener
        ) as build:
            result = fetch_public_text("https://example.com/", {"example.com"})
        self.assertEqual(result["text"], "Public")
        self.assertTrue(result["content_is_untrusted_data"])
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(build.call_args.args[0].proxies, {})
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 10)

    def test_rejects_non_html(self):
        response = self.response(b"{}", "application/json")
        opener = Mock()
        opener.open.return_value = response
        with patch("socket.getaddrinfo", public_dns), patch(
            "grvis_safe_web_reader.core.build_opener", return_value=opener
        ), self.assertRaisesRegex(RuntimeError, "not HTML"):
            fetch_public_text("https://example.com/", {"example.com"})

    def test_enforces_response_byte_limit(self):
        response = self.response(b"x" * (MAX_RESPONSE_BYTES + 1))
        opener = Mock()
        opener.open.return_value = response
        with patch("socket.getaddrinfo", public_dns), patch(
            "grvis_safe_web_reader.core.build_opener", return_value=opener
        ), self.assertRaisesRegex(RuntimeError, "2 MiB"):
            fetch_public_text("https://example.com/", {"example.com"})
        response.read.assert_called_once_with(MAX_RESPONSE_BYTES + 1)

    def test_preserves_long_text_and_structured_fields(self):
        body = ('<html><title>Report</title><body><p>' + 'z' * 60000 +
                '</p><a href="/next">Next</a><img src="/photo.png" alt="photo">'
                '<table><tr><th>Name</th></tr><tr><td>Big</td></tr></table></body></html>').encode()
        opener = Mock()
        opener.open.return_value = self.response(body)
        with patch("socket.getaddrinfo", public_dns), patch(
            "grvis_safe_web_reader.core.build_opener", return_value=opener
        ):
            result = fetch_public_text("https://example.com/", {"example.com"})
        self.assertGreater(len(result["text"]), 50000)
        self.assertEqual(''.join(result["text_chunks"]), result["text"])
        self.assertFalse(result["truncated"])
        self.assertEqual(result["links"][0]["url"], "https://example.com/next")
        self.assertEqual(result["tables"], [[["Name"], ["Big"]]])

    def test_redirect_rechecks_destination_allowlist(self):
        headers = Message()
        headers["Location"] = "https://unapproved.example/"
        opener = Mock()
        opener.open.side_effect = HTTPError("https://example.com/", 302, "Found", headers, None)
        with patch("socket.getaddrinfo", public_dns), patch(
            "grvis_safe_web_reader.core.build_opener", return_value=opener
        ), self.assertRaisesRegex(SafetyError, "allowlist"):
            fetch_public_text("https://example.com/", {"example.com"})
        self.assertEqual(opener.open.call_count, 1)

    def test_redirect_to_approved_host_is_followed(self):
        headers = Message()
        headers["Location"] = "/next"
        opener = Mock()
        opener.open.side_effect = [HTTPError("https://example.com/", 302, "Found", headers, None),
                                   self.response(b"<html><body>Next</body></html>")]
        with patch("socket.getaddrinfo", public_dns), patch(
            "grvis_safe_web_reader.core.build_opener", return_value=opener
        ):
            result = fetch_public_text("https://example.com/", {"example.com"})
        self.assertEqual(result["source_url"], "https://example.com/next")
        self.assertEqual(result["redirect_chain"], ["https://example.com/next"])


if __name__ == "__main__":
    unittest.main()
