import unittest
from app.schemas.sefaz import SefazRequest, SefazErrorCategory
from app.services.sefaz_adapter import SefazServiceAdapter
from app.services.sefaz_endpoints import get_sefaz_url


class TestSefazAdapter(unittest.TestCase):
    def test_sefaz_autorizar_success(self):
        sample_xml = '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe Id="NFe35260912345678000199550010000000011123456781" versao="4.00"></infNFe></NFe>'
        
        req = SefazRequest(
            xml_content=sample_xml,
            uf="SP",
            environment=2,
            doc_model="55",
            timeout_seconds=10.0,
            max_retries=1,
            use_mock_in_homologation=True,
        )

        resp = SefazServiceAdapter.autorizar_nfe(req)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status_code, 100)
        self.assertEqual(resp.reason, "Autorizado o uso da NF-e")
        self.assertIsNotNone(resp.protocol_number)
        self.assertIsNotNone(resp.digest_value)
        self.assertEqual(resp.error_category, SefazErrorCategory.NONE)

    def test_sefaz_rejection_normalized(self):
        sample_xml_rej = '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe Id="NFe35260912345678000199550010000000011123459999" versao="4.00"></infNFe></NFe>'
        
        req = SefazRequest(
            xml_content=sample_xml_rej,
            uf="SP",
            environment=2,
            doc_model="55",
            use_mock_in_homologation=True,
        )

        resp = SefazServiceAdapter.autorizar_nfe(req)
        self.assertFalse(resp.success)
        self.assertEqual(resp.status_code, 204)
        self.assertIn("Duplicidade", resp.reason)
        self.assertEqual(resp.error_category, SefazErrorCategory.SEFAZ_REJECTION)

    def test_sefaz_consultar_nfe(self):
        valid_key = "35260912345678000199550010000000011123456781"
        resp = SefazServiceAdapter.consultar_nfe(access_key=valid_key, uf="SP", environment=2)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status_code, 100)
        self.assertEqual(resp.access_key, valid_key)

        invalid_key = "123"
        resp_inv = SefazServiceAdapter.consultar_nfe(access_key=invalid_key, uf="SP", environment=2)
        self.assertFalse(resp_inv.success)
        self.assertEqual(resp_inv.status_code, 215)

    def test_sefaz_status_servico(self):
        resp = SefazServiceAdapter.consultar_status_servico(uf="SP", environment=2)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status_code, 107)
        self.assertIn("Serviço em Operação", resp.reason)

    def test_sefaz_endpoint_url_resolution(self):
        url_sp_hom = get_sefaz_url("SP", "NfeAutorizacao4", environment=2)
        self.assertIn("homologacao.nfe.fazenda.sp.gov.br", url_sp_hom)

        url_sp_prod = get_sefaz_url("SP", "NfeAutorizacao4", environment=1)
        self.assertIn("nfe.fazenda.sp.gov.br", url_sp_prod)

        url_svrs = get_sefaz_url("RJ", "NfeAutorizacao4", environment=2)
        self.assertIn("svrs.rs.gov.br", url_svrs)


if __name__ == "__main__":
    unittest.main()
