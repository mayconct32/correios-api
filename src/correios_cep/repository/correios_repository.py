from src.correios_cep.interfaces import IDatabaseConnection, ICorreiosRepository
from src.correios_cep.model.address import Address


class CorreiosRepository(ICorreiosRepository):
    """
    Repositório de endereços: apenas acesso a dados.

    Não contém regras de negócio — retorna o que o banco tem (ou None /
    lista vazia) e deixa as decisões de caso de uso para o Service.
    """

    def __init__(self, db_connection: IDatabaseConnection):
        self._db_connection = db_connection

    async def find_by_zipcode(self, zipcode: str) -> Address | None:
        """
        Busca um endereço pelo CEP.

        Parâmetros:
            zipcode (str): CEP com 8 dígitos.

        Retorna:
            Address | None: endereço encontrado, ou None quando o CEP
                não existir.
        """
        sql = """
            SELECT zipcode, state, city, neighborhood, street
            FROM addresses
            WHERE zipcode = %s
            LIMIT 1
        """
        rows = await self._db_connection.query(sql=sql, data=(zipcode,))
        return Address(**rows[0]) if rows else None

    async def find_by_city(self, city: str) -> list[Address]:
        """
        Busca todos os endereços de uma cidade.

        Parâmetros:
            city (str): nome da cidade.

        Retorna:
            list[Address]: endereços encontrados (pode ser vazia).
        """
        sql = """
            SELECT zipcode, state, city, neighborhood, street
            FROM addresses
            WHERE city = %s
        """
        rows = await self._db_connection.query(sql=sql, data=(city,))
        return [Address(**row) for row in rows]
