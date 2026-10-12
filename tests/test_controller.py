import pytest_asyncio
import pytest
from http import HTTPStatus
from httpx import AsyncClient, ASGITransport
from src.correios_cep.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://lobotest"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_by_zip_code(client):
    zipcode = "36803000"
    response = await client.get(f"/zip/{zipcode}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "state": "MG",
        "city": "Carangola",
        "neighborhood": "Alvorada",
        "zipcode": "36803000",
        "street": ""
    }


@pytest.mark.asyncio
async def test_get_by_zip_code_empty_validation(client):
    response = await client.get("/zip/")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "detail": "CEP não pode ser vazio"
    }


@pytest.mark.asyncio
async def test_get_by_zip_code_404(client):
    zipcode = "00000000"
    response = await client.get(f"/zip/{zipcode}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "detail": f"CEP {zipcode} não encontrado"
    }



@pytest.mark.asyncio
async def test_get_by_city_200(client):
    response = await client.get("/city/Carangola")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(),list)


@pytest.mark.asyncio
async def test_get_by_city_with_limit(client):
    response = await client.get("/city/Carangola", params={"limit": 2})
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)
    assert len(response.json()) <= 2


@pytest.mark.asyncio
async def test_get_by_city_limit_zero(client):
    response = await client.get("/city/Carangola", params={"limit": 0})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "detail": "Limite deve ser maior que zero"
    }


@pytest.mark.asyncio
async def test_get_by_city_limit_above_max(client):
    response = await client.get("/city/Carangola", params={"limit": 501})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "detail": "Limite não pode ser maior que 500"
    }


@pytest.mark.asyncio
async def test_get_by_city_404(client):
    city = "invalid_city"
    response = await client.get(f"city/{city}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "detail": f"Nenhum endereço em {city}"
    }


@pytest.mark.asyncio
async def test_get_by_city_empty_validation(client):
    response = await client.get("/city/")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "detail": "Cidade não pode ser vazia"
    }


@pytest.mark.asyncio
async def test_healt_check_200(client):
    response = await client.get("/health_check")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "message": "OK",
        "status": "healthy",
        "database": "connected"
    }
