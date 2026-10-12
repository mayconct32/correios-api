from src.correios_cep.interfaces import IDatabaseConnection, ISetupRepository


class SetupRepository(ISetupRepository):
    def __init__(self, db_connection: IDatabaseConnection):
        self._db_connection = db_connection

    async def insert_address(self, file_path: str) -> bool:
        """
        Insere endereços no banco a partir de um arquivo CSV em disco.

        Parâmetros:
            file_path (str): caminho do arquivo CSV carregado via
                comando LOAD DATA.

        Retorna:
            bool: True quando a operação de carga é executada sem erros.
        """
        await self._db_connection.execute(
            sql="""
                LOAD DATA LOCAL INFILE %s
                INTO TABLE addresses
                FIELDS TERMINATED BY ','
                OPTIONALLY ENCLOSED BY '"'
                LINES TERMINATED BY '\\n'
                (state, city, neighborhood, zipcode, street, @i1, @i2, @i3, @i4, @i5, @i6, @i7, @i8, @i9, @i10)
            """,
            data=(file_path,),
        )
        return True

    async def check_postal_codes_exist(self) -> bool:
        """
        Verifica se já existem registros de CEP na tabela de endereços.

        Parâmetros:
            Nenhum.

        Retorna:
            bool: True se houver ao menos um registro de CEP, senão
                False.
        """
        response = await self._db_connection.execute(
            sql="""
                SELECT COUNT(*) as count
                FROM addresses
            """
        )
        count = response[0]["count"]
        return count > 0

