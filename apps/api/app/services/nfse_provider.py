from typing import Dict, Type
from app.services.nfse_adapters.base_adapter import BaseNfseAdapter
from app.services.nfse_adapters.national_adapter import NationalNfseAdapter
from app.services.nfse_adapters.abrasf_v2_adapter import AbrasfV2Adapter
from app.services.nfse_adapters.paulistana_adapter import PaulistanaNfseAdapter


class NfseProviderFactory:
    """
    Fábrica e Resolvedor de Provedores de NFS-e (Factory Pattern).
    Seleciona dinamicamente o adapter de transmissão por município ou padrão fiscal configurado.
    """
    _adapters: Dict[str, Type[BaseNfseAdapter]] = {
        "NATIONAL": NationalNfseAdapter,
        "ABRASF_V2": AbrasfV2Adapter,
        "PAULISTANA": PaulistanaNfseAdapter,
    }

    @classmethod
    def get_adapter(cls, provider_type: str = "NATIONAL") -> BaseNfseAdapter:
        provider_key = (provider_type or "NATIONAL").upper().strip()
        adapter_cls = cls._adapters.get(provider_key, NationalNfseAdapter)
        return adapter_cls()

    @classmethod
    def register_adapter(cls, provider_key: str, adapter_cls: Type[BaseNfseAdapter]) -> None:
        cls._adapters[provider_key.upper().strip()] = adapter_cls
