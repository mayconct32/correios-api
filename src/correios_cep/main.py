import logging
from http import HTTPStatus
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from src.correios_cep.controller.correios_controller import app as correios
from src.correios_cep.container import container
from src.correios_cep.exceptions import AppException


# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(levelname)s - \033[93m%(message)s\033[m"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação e garante o carregamento dos
    dados de CEP.

    Parâmetros:
        app (FastAPI): instância principal da aplicação FastAPI.

    Retorna:
        AsyncIterator[None]: contexto assíncrono usado pelo FastAPI no
            ciclo de vida.
    """
    logger.info("=" * 60)
    logger.info("Iniciando aplicação - Carregando dados de CEP")
    logger.info("=" * 60)
    
    try:
        setup_repository = container.get_setup_repository()
        
        # Garante que a tabela de endereços exista
        await setup_repository.create_addresses_table()
        
        # Verifica se dados já estão carregados
        dados_existem = await setup_repository.check_postal_codes_exist()
        
        if dados_existem:
            logger.info("✓ Dados de CEP já carregados no banco de dados")
        else:
            logger.info("Iniciando download do arquivo CSV...")
            
            import_service = container.get_postal_code_import_service()
            await import_service.import_postal_codes()
            
            logger.info("✓ Arquivo CSV importado com sucesso no banco de dados")
    
    except AppException as e:
        logger.error(f"Erro na aplicação: {e.message}")
    except Exception as e:
        logger.error(f"Erro inesperado durante inicialização: {str(e)}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info("Aplicação iniciada e pronta para receber requisições")
    logger.info("=" * 60)
    yield

    logger.info("Encerrando aplicação - fechando pool de conexões do banco")
    try:
        db_connection = container.get_db_connection()
        await db_connection.close()
        logger.info("✓ Pool de conexões encerrado")
    except Exception as e:
        logger.warning(f"Erro ao encerrar pool de conexões: {e}")
    logger.info("Aplicação encerrada")


app = FastAPI(
    lifespan=lifespan, 
    title="Correios CEP API", 
    version="1.0.0"
)


@app.exception_handler(AppException)
async def exception_handler(request: Request, exc: AppException):
    """
    Trata exceções de domínio e as converte em respostas HTTP.

    Parâmetros:
        request (Request): requisição HTTP que gerou a exceção.
        exc (AppException): exceção de domínio capturada pela
            aplicação.

    Retorna:
        JSONResponse: resposta HTTP com código de status e mensagem de
            erro.
    """
    logger.warning(f"Exceção capturada: [{exc.status_code}] {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.get("/health_check", status_code=HTTPStatus.OK)
async def health_check():
    """
    Verifica a saúde da aplicação, incluindo conexão com o banco de dados.

    Parâmetros:
        Nenhum.

    Retorna:
        dict: informações sobre o status geral da aplicação e do banco.
    """
    try:
        db = container.get_db_connection()
        await db.query("SELECT 1")
        
        return {
            "message": "OK",
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check falhou: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )


app.include_router(correios)