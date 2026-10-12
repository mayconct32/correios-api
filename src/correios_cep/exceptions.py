
class AppException(Exception):
    """
    Exceção base da aplicação com status_code e mensagem personalizados.

    Todas as demais exceções específicas devem herdar desta classe para
    que o handler global consiga tratá-las de forma padronizada.
    """

    # valores padrão podem ser sobrescritos nas subclasses
    status_code: int = 500
    default_message: str = "Erro na aplicação"

    def __init__(self, message: str | None = None,
                 status_code: int | None = None):
        """
        Inicializa a exceção com código de status e mensagem padrão.

        Parâmetros:
            message (str | None): mensagem de erro específica, opcional.
            status_code (int | None): código HTTP a ser exposto, opcional.

        Retorna:
            None.
        """
        self.status_code = status_code or self.__class__.status_code
        self.message = message or self.__class__.default_message
        super().__init__(self.message)


class DatabaseException(AppException):
    """
    Exceção relacionada a operações de banco de dados.

    A mensagem deve permanecer genérica: detalhes do driver (host,
    usuário, SQL etc.) não podem ser expostos ao cliente — devem ser
    registrados nos logs no ponto em que o erro ocorre.
    """
    status_code = 500
    default_message = "Erro ao acessar banco de dados"


class AddressNotFoundException(AppException):
    """Exceção lançada quando um endereço não é encontrado"""
    status_code = 404
    default_message = "Registro não encontrado"


class CSVException(AppException):
    """
    Exceção base para erros relacionados ao processamento de arquivos
    CSV na aplicação.
    """


class CSVDownloadException(CSVException):
    """Exceção lançada quando há erro ao fazer download do CSV"""
    status_code = 500
    default_message = "Erro ao processar arquivo"


class CSVFileException(CSVException):
    """Exceção lançada quando há erro com arquivo CSV"""
    status_code = 500
    default_message = "Erro ao processar arquivo"
