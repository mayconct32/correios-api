from http import HTTPStatus
from fastapi import APIRouter, Depends
from src.correios_cep.service.correios_service import CorreiosService
from src.correios_cep.container import container
from src.correios_cep.exceptions import AppException
from src.correios_cep.model.address import Address


app = APIRouter()


def get_correios_service() -> CorreiosService:
    """
    Retorna a instância de CorreiosService provida pelo container.

    Parâmetros:
        Nenhum.

    Retorna:
        CorreiosService: serviço utilizado para consultas de endereços.
    """
    return container.get_correios_service()


@app.get("/zip/{zipcode}", response_model=Address)
async def get_by_zip_code(
    zipcode: str,
    service: CorreiosService = Depends(get_correios_service)
):
    """
    Retorna o endereço associado ao CEP informado.

    Parâmetros:
        zipcode (str): código de CEP usado na consulta.
        service (CorreiosService): serviço responsável pela busca.

    Retorna:
        Address: dados do endereço correspondente ao CEP.
    """
    return await service.get_address_by_postal_code(zipcode=zipcode)


@app.get("/zip/")
async def get_by_zip_code_empty():
    """
    Trata requisições sem CEP informado.

    A rota /zip/{zipcode} não captura o caminho vazio; sem este handler,
    a requisição receberia 404 em vez de uma mensagem de validação.

    Parâmetros:
        Nenhum.

    Lança:
        AppException: erro 400 indicando que o CEP é obrigatório.
    """
    raise AppException("CEP não pode ser vazio", status_code=HTTPStatus.BAD_REQUEST)


@app.get("/city/{city}", response_model=list[Address])
async def get_by_city(
    city: str,
    service: CorreiosService = Depends(get_correios_service)
):
    """
    Retorna todos os endereços pertencentes à cidade informada.

    Parâmetros:
        city (str): nome da cidade usada como filtro.
        service (CorreiosService): serviço responsável pela busca.

    Retorna:
        list[Address]: lista de endereços encontrados para a cidade.
    """
    return await service.get_address_by_city(city=city)


@app.get("/city/")
async def get_by_city_empty():
    """
    Trata requisições sem cidade informada.

    A rota /city/{city} não captura o caminho vazio; sem este handler,
    a requisição receberia 404 em vez de uma mensagem de validação.

    Parâmetros:
        Nenhum.

    Lança:
        AppException: erro 400 indicando que a cidade é obrigatória.
    """
    raise AppException("Cidade não pode ser vazia", status_code=HTTPStatus.BAD_REQUEST)
