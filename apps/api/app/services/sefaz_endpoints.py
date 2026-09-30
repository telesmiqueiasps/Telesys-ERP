"""
Tabela de URLs dos WebServices da SEFAZ v4.00 por UF e Ambiente.
Ambiente 1 = Produção
Ambiente 2 = Homologação
"""

SEFAZ_ENDPOINTS = {
    "SP": {
        1: {  # Produção
            "NfeAutorizacao4": "https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
            "NfeRetAutorizacao4": "https://nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx",
            "NfeConsultaProtocolo4": "https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx",
            "NfeStatusServico4": "https://nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx",
        },
        2: {  # Homologação
            "NfeAutorizacao4": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
            "NfeRetAutorizacao4": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx",
            "NfeConsultaProtocolo4": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx",
            "NfeStatusServico4": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx",
        }
    },
    "SVRS": {  # SEFAZ Virtual RS (Atende RS, SC, PR, RJ, etc. quando aplicável)
        1: {
            "NfeAutorizacao4": "https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx",
            "NfeRetAutorizacao4": "https://nfe.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx",
            "NfeConsultaProtocolo4": "https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NFeConsulta4.asmx",
            "NfeStatusServico4": "https://nfe.svrs.rs.gov.br/ws/NfeStatusServico/NFeStatusServico4.asmx",
        },
        2: {
            "NfeAutorizacao4": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx",
            "NfeRetAutorizacao4": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx",
            "NfeConsultaProtocolo4": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeConsulta/NFeConsulta4.asmx",
            "NfeStatusServico4": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeStatusServico/NFeStatusServico4.asmx",
        }
    }
}


def get_sefaz_url(uf: str, service_name: str, environment: int = 2) -> str:
    """
    Retorna a URL do WebService da SEFAZ para a UF, Serviço e Ambiente.
    Se a UF específica não estiver na tabela, faz fallback para SVRS.
    """
    clean_uf = uf.upper().strip()
    env_dict = SEFAZ_ENDPOINTS.get(clean_uf, SEFAZ_ENDPOINTS["SVRS"])
    services = env_dict.get(environment, env_dict[2])
    return services.get(service_name, services["NfeAutorizacao4"])
