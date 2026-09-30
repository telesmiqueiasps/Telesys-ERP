import unittest
import uuid
from datetime import datetime, timezone, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

from app.core.crypto import encrypt_data, decrypt_text
from app.services.company_fiscal import parse_and_validate_pkcs12

class TestFiscalCompanyConfig(unittest.TestCase):
    def test_fernet_encryption_decryption(self):
        original = "senha_super_secreta_123"
        encrypted = encrypt_data(original)
        self.assertNotEqual(original, encrypted)
        decrypted = decrypt_text(encrypted)
        self.assertEqual(original, decrypted)

    def test_pkcs12_parser_with_synthetic_cert(self):
        # Generate self-signed RSA key & cert
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA TESTE LTDA:12345678000199"),
        ])
        valid_until = datetime.now(timezone.utc) + timedelta(days=365)
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc) - timedelta(days=1)
        ).not_valid_after(
            valid_until
        ).sign(key, hashes.SHA256())

        pfx_data = pkcs12.serialize_key_and_certificates(
            name=b"cert",
            key=key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(b"password123")
        )

        cert_obj, subject_cn, subject_cnpj, issuer_cn, serial_number, v_from, v_until = parse_and_validate_pkcs12(pfx_data, "password123")
        self.assertIn("12345678000199", subject_cnpj)
        self.assertEqual(subject_cn, "EMPRESA TESTE LTDA:12345678000199")
        self.assertGreater((v_until - datetime.now(timezone.utc)).days, 300)

if __name__ == "__main__":
    unittest.main()
