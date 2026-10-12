import logging
import os
from dotenv import load_dotenv
from mysql.connector.aio import pooling
from src.correios_cep.exceptions import DatabaseException
from src.correios_cep.interfaces import IDatabaseConnection


load_dotenv(override=True)

logger = logging.getLogger(__name__)


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
                logger.error(f"Erro ao criar pool de conexões: {e}")
                raise DatabaseException("Erro ao criar pool de conexões") from e
        return self._pool

    async def query(self, sql: str, data=None) -> list[dict]:
        """
        Executa uma consulta (SELECT) usando uma conexão do pool.

        Args:
            sql: Query SQL de consulta.
            data: Parâmetros da query.

        Returns:
            Lista de dicionários com as linhas encontradas.

        Raises:
            DatabaseException: Em falhas de conexão ou execução.
        """
        pool = await self._get_pool()
        try:
            connection = await pool.get_connection()
        except Exception as e:
            logger.error(f"Erro ao obter conexão do pool: {e}")
            raise DatabaseException("Erro ao obter conexão do pool") from e

        try:
            async with await connection.cursor(dictionary=True) as cursor:
                await cursor.execute(sql, data)
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao executar consulta: {e}")
            raise DatabaseException("Erro ao executar consulta") from e
        finally:
            await connection.close()  # devolve a conexão ao pool

    async def execute(self, sql: str, data=None) -> None:
        """
        Executa uma operação de escrita (INSERT/UPDATE/DELETE/DDL)
        usando uma conexão do pool e confirma a transação.

        Args:
            sql: Query SQL de escrita.
            data: Parâmetros da query.

        Returns:
            None.

        Raises:
            DatabaseException: Em falhas de conexão ou execução.
        """
        pool = await self._get_pool()
        try:
            connection = await pool.get_connection()
        except Exception as e:
            logger.error(f"Erro ao obter conexão do pool: {e}")
            raise DatabaseException("Erro ao obter conexão do pool") from e

        try:
            async with await connection.cursor(dictionary=True) as cursor:
                await cursor.execute(sql, data)
            await connection.commit()
        except Exception as e:
            logger.error(f"Erro ao executar operação: {e}")
            raise DatabaseException("Erro ao executar operação") from e
        finally:
            await connection.close()  # devolve a conexão ao pool

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
