from src.correios_cep.database import MysqlDBConnection
from src.correios_cep.interfaces import IDatabaseConnection, ISetupRepository, ICorreiosRepository
from src.correios_cep.repository.correios_repository import CorreiosRepository
from src.correios_cep.repository.setup_repository import SetupRepository
from src.correios_cep.service.correios_service import CorreiosService
from src.correios_cep.service.csvfile_service import (
    CSVDownloadService,
    CSVFileService,
    PostalCodeImportService
)


class Container:
    """
    Container singleton responsável por montar as dependências da
    aplicação.

    Parâmetros:
        Nenhum.

    Retorna:
        Container: instância única para resolver serviços e repositórios.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Container, cls).__new__(cls)
            cls._instance._db_connection = None
            cls._instance._setup_repository = None
            cls._instance._correios_repository = None
        return cls._instance
    
    def get_db_connection(self) -> IDatabaseConnection:
        """
        Retorna a conexão (pool) compartilhada com o banco de dados MySQL,
        criando-a apenas na primeira chamada.

        Parâmetros:
            Nenhum.

        Retorna:
            IDatabaseConnection: mesma instância de pool em todas as
                chamadas, evitando uma conexão nova por requisição.
        """
        if self._db_connection is None:
            self._db_connection = MysqlDBConnection()
        return self._db_connection

    def get_setup_repository(self) -> ISetupRepository:
        """
        Retorna o SetupRepository compartilhado, criando-o apenas na
        primeira chamada.

        Parâmetros:
            Nenhum.

        Retorna:
            ISetupRepository: repositório para carga e verificação de
                CEPs.
        """
        if self._setup_repository is None:
            self._setup_repository = SetupRepository(self.get_db_connection())
        return self._setup_repository

    def get_correios_repository(self) -> ICorreiosRepository:
        """
        Retorna o CorreiosRepository compartilhado, criando-o apenas na
        primeira chamada.

        Parâmetros:
            Nenhum.

        Retorna:
            ICorreiosRepository: repositório usado nas consultas de
                endereços.
        """
        if self._correios_repository is None:
            self._correios_repository = CorreiosRepository(self.get_db_connection())
        return self._correios_repository
    
    def get_correios_service(self) -> CorreiosService:
        """
        Cria uma instância de CorreiosService com repositório injetado.

        Parâmetros:
            Nenhum.

        Retorna:
            CorreiosService: serviço de domínio usado pelos controllers
                da API.
        """
        return CorreiosService(self.get_correios_repository())
    
    def get_postal_code_import_service(self) -> PostalCodeImportService:
        """
        Cria um PostalCodeImportService pronto para importar CEPs via
        CSV.

        Parâmetros:
            Nenhum.

        Retorna:
            PostalCodeImportService: serviço que orquestra a carga de
                CEPs.
        """
        csv_url = "https://raw.githubusercontent.com/miltonhit/miltonhit/main/public-assets/cep-20190602.csv"
        csv_download = CSVDownloadService(csv_url)
        csv_file = CSVFileService()
        
        return PostalCodeImportService(
            csv_download_service=csv_download,
            csv_file_service=csv_file,
            setup_repository=self.get_setup_repository()
        )


# Instância global do container
container = Container()