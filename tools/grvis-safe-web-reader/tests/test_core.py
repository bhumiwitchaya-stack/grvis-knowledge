import socket
import unittest
from unittest.mock import patch

from grvis_safe_web_reader.core import SafetyError, canonical_hostname, validate_url


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


if __name__ == "__main__":
    unittest.main()
