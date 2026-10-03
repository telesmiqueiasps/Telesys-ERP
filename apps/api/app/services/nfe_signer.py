import base64
import hashlib
import re
from xml.etree import ElementTree as ET
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12


class NfeSigner:
    @staticmethod
    def sign_xml(raw_xml_str: str, pfx_bytes: bytes, password: str) -> str:
        return NfeSigner.sign_nfe_xml(raw_xml_str, pfx_bytes, password)

    @staticmethod
    def sign_nfe_xml(raw_xml_str: str, pfx_bytes: bytes, password: str) -> str:
        """
        Assina digitalmente o XML da NF-e / NFC-e / Evento no nó <infNFe> ou <infEvento> / <infInut>
        usando o certificado A1 PKCS12 (.pfx/.p12) conforme padrão W3C XML Digital Signature.
        """
        private_key, cert, _ = pkcs12.load_key_and_certificates(
            pfx_bytes, password.encode("utf-8") if password else None
        )
        if not cert or not private_key:
            raise ValueError("Não foi possível carregar a chave privada ou certificado A1 para a assinatura digital.")

        # Extrair o ID do elemento (NFe..., ID..., DPS...)
        id_match = re.search(r'Id="((?:NFe|ID|DPS)[a-zA-Z0-9]+)"', raw_xml_str)
        if not id_match:
            raise ValueError("ID da tag de assinatura (<infNFe>, <infEvento>, <infInut> ou <infDPS>) não encontrado no XML.")

        element_id = id_match.group(1)
        ref_uri = f"#{element_id}"

        # Extrair a string do elemento assinado para canonização C14N
        inf_match = re.search(r'(<(?:infNFe|infEvento|infInut|infDPS) Id=".*?</(?:infNFe|infEvento|infInut|infDPS)>)', raw_xml_str, re.DOTALL)
        if not inf_match:
            raise ValueError("Não foi possível isolar a tag interna do XML para canonização.")

        inf_str = inf_match.group(1)

        # 1. Calcular o DigestValue SHA-1 do elemento isolado
        digest_bytes = hashlib.sha1(inf_str.encode("utf-8")).digest()
        digest_b64 = base64.b64encode(digest_bytes).decode("utf-8")

        # 2. Constrói a tag <SignedInfo>
        signed_info_xml = f"""<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
<Reference URI="{ref_uri}">
<Transforms>
<Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
<Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
</Transforms>
<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
<DigestValue>{digest_b64}</DigestValue>
</Reference>
</SignedInfo>"""

        # 3. Assinar o <SignedInfo> com a chave privada RSA
        signed_info_bytes = signed_info_xml.encode("utf-8")
        signature_bytes = private_key.sign(
            signed_info_bytes,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8").replace("\n", "")

        # 4. Certificado X.509 em base64
        cert_der = cert.public_bytes(serialization.Encoding.DER)
        cert_b64 = base64.b64encode(cert_der).decode("utf-8").replace("\n", "")

        # 5. Estrutura W3C Signature completa
        signature_node = f"""<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
{signed_info_xml}
<SignatureValue>{signature_b64}</SignatureValue>
<KeyInfo>
<X509Data>
<X509Certificate>{cert_b64}</X509Certificate>
</X509Data>
</KeyInfo>
</Signature>"""

        # Inserir o nó <Signature> antes da tag de fechamento correspondente
        if "</evento>" in raw_xml_str:
            signed_xml = raw_xml_str.replace("</evento>", f"{signature_node}\n</evento>")
        elif "</inutNFe>" in raw_xml_str:
            signed_xml = raw_xml_str.replace("</inutNFe>", f"{signature_node}\n</inutNFe>")
        elif raw_xml_str.endswith("</NFe>"):
            signed_xml = raw_xml_str[:-6] + f"\n{signature_node}\n</NFe>"
        else:
            signed_xml = raw_xml_str + f"\n{signature_node}"

        return signed_xml
