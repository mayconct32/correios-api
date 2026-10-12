import os
from dotenv import load_dotenv
from mysql.connector.aio import pooling
from src.correios_cep.exceptions import DatabaseException
from src.correios_cep.interfaces import IDatabaseConnection


load_dotenv(override=True)


class MysqlDBConnection(IDatabaseConnection):
    """
    Conexão com o MySQL por meio de um pool assíncrono compartilhado.

    O pool é criado na primeira operação (lazy) e reutilizado por toda a
    aplicação. Cada operação pega uma conexão do pool, usa e a devolve ao
    final, evitando abrir uma conexão nova por requisição sem nunca fechar
    as antigas.
    """

    def __init__(self, pool_size: int = 5):
        self._host = os.getenv("HOST")
        self._user = os.getenv("USER")
        self._password = os.getenv("PASSWORD")
        self._database = os.getenv("DATABASE")
        self._pool_size = pool_size
        self._pool = None

    def _config(self) -> dict:
        """
        Monta a configuração do pool a partir das variáveis de ambiente.

        Parâmetros:
            Nenhum.

        Retorna:
            dict: parâmetros de conexão aceitos pelo driver MySQL.

        Lança:
            DatabaseException: quando variáveis obrigatórias ausentes.
        """
        if not all([self._host, self._user, self._password, self._database]):
            raise DatabaseException("Variáveis de ambiente do banco de dados não configuradas")
        return {
            "host": self._host,
            "user": self._user,
            "password": self._password,
            "database": self._database,
            "allow_local_infile": True,
        }

    async def _get_pool(self) -> pooling.MySQLConnectionPool:
        """
        Retorna o pool de conexões, criando-o na primeira utilização.

        Parâmetros:
            Nenhum.

        Retorna:
            MySQLConnectionPool: pool assíncrono pronto para uso.

        Lança:
            DatabaseException: quando não for possível criar o pool.
        """
        if self._pool is None:
            try:
                self._pool = pooling.MySQLConnectionPool(
                    pool_name="correios_pool",
                    pool_size=self._pool_size,
                    **self._config()
                )
            except Exception as e:
                raise DatabaseException(f"Erro ao criar pool de conexões: {e}") from e
        return self._pool

    async def _run(self, sql: str, data=None, operation="SELECT") -> list[dict] | None:
        """
        Executa uma operação usando uma conexão emprestada do pool.

        Parâmetros:
            sql (str): query SQL a ser executada.
            data: parâmetros da query.
            operation (str): "SELECT" retorna as linhas; demais valores
                apenas executam e confirmam a transação.

        Retorna:
            list[dict] | None: linhas para SELECT; None para escritas.

        Lança:
            DatabaseException: em falhas de conexão ou execução.
        """
        pool = await self._get_pool()
        try:
            connection = await pool.get_connection()
        except Exception as e:
            raise DatabaseException(f"Erro ao obter conexão do pool: {e}") from e

        try:
            async with await connection.cursor(dictionary=True) as cursor:
                await cursor.execute(sql, data)
                if operation == "SELECT":
                    return await cursor.fetchall()
                await connection.commit()
        except Exception as e:
            raise DatabaseException(f"Erro ao executar operação: {e}") from e
        finally:
            await connection.close()  # devolve a conexão ao pool

    async def execute(
        self,
        sql: str,
        data=None,
        operation="SELECT"
    ):
        """
        Executa uma query SQL.

        Args:
            sql: Query SQL a ser executada.
            data: Parâmetros da query.
            operation: "SELECT" retorna linhas; demais executam e commitam.

        Returns:
            Lista de dicionários para SELECT; None para operações de escrita.
        """
        return await self._run(sql=sql, data=data, operation=operation)

    async def close(self) -> None:
        """
        Encerra todas as conexões do pool.

        Deve ser chamado no shutdown da aplicação.

        Parâmetros:
            Nenhum.

        Retorna:
            None.
        """
        if self._pool is not None:
            await self._pool.close_pool()
            self._pool = None
