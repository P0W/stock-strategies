import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.oid import NameOID

# Generate a private key
private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

# Serialize the private key to PEM format
private_key_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)

# Save the private key to a file (key.pem)
with open("key.pem", "wb") as key_file:
    key_file.write(private_key_pem)

# Generate a self-signed certificate
subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName("example.com")]),
        critical=False,
    )
    .sign(private_key, hashes.SHA256(), default_backend())
)

# Serialize the certificate to PEM format
cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)

# Save the certificate to a file (cert.pem)
with open("cert.pem", "wb") as cert_file:
    cert_file.write(cert_pem)
