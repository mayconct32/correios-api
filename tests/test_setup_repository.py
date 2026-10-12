import pytest
from src.correios_cep.interfaces import IDatabaseConnection
from src.correios_cep.repository.setup_repository import SetupRepository


class FakeDBConnection(IDatabaseConnection):
    """
    Conexão fake para testes: retorna resultado pré-configurado para
    query e registra o SQL recebido por execute.
    """

    def __init__(self, query_result: list[dict] | None = None):
        self._query_result = query_result or []
        self.executed_sqls: list[str] = []

    async def query(self, sql: str, data: tuple = ()) -> list[dict]:
        return self._query_result

    async def execute(self, sql: str, data: tuple = ()) -> None:
        self.executed_sqls.append(sql)

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_create_addresses_table_executes_script():
    db = FakeDBConnection()
    repository = SetupRepository(db_connection=db)

    await repository.create_addresses_table()

    assert len(db.executed_sqls) == 1
    assert "CREATE TABLE IF NOT EXISTS addresses" in db.executed_sqls[0]
