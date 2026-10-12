from src.correios_cep.interfaces import ICorreiosRepository
from src.correios_cep.exceptions import AddressNotFoundException
from src.correios_cep.model.address import Address


class CorreiosService:
    """
    Serviço de domínio: concentra as regras de negócio das consultas de
    endereço e decide quando um resultado é "não encontrado".

    Parâmetros:
        correios_repository (ICorreiosRepository): repositório usado
            nas consultas de CEP e cidade.
    """

    def __init__(self, correios_repository: ICorreiosRepository):
        """
        Inicializa o serviço de domínio com o repositório de endereços.

        Parâmetros:
            correios_repository (ICorreiosRepository): repositório usado
                nas consultas de CEP e cidade.

        Retorna:
            None.
        """
        self._correios_repository = correios_repository

    async def get_address_by_postal_code(self, zipcode: str) -> Address:
        """
        Retorna o endereço correspondente a um CEP específico.

        Parâmetros:
            zipcode (str): CEP usado como filtro principal da consulta.

        Retorna:
            Address: endereço retornado pelo repositório para o CEP
            informado.

        Lança:
            AddressNotFoundException: quando o CEP não é encontrado.
        """
        address = await self._correios_repository.find_by_zipcode(zipcode=zipcode)
        if address is None:
            raise AddressNotFoundException(f"CEP {zipcode} não encontrado")
        return address

    async def get_address_by_city(self, city: str) -> list[Address]:
        """
        Retorna todos os endereços localizados em uma cidade.

        Parâmetros:
            city (str): nome da cidade usado como filtro da consulta.

        Retorna:
            list[Address]: lista de endereços encontrados para a cidade.

        Lança:
            AddressNotFoundException: quando a cidade não tem endereços.
        """
        addresses = await self._correios_repository.find_by_city(city=city)
        if not addresses:
            raise AddressNotFoundException(f"Nenhum endereço em {city}")
        return addresses
