# Correios CEP API

API REST para consulta de CEPs brasileiros. Os dados de endereço são
carregados a partir de um arquivo CSV público e servidos via MySQL,
com busca por CEP e por cidade.

## Funcionalidades

- Consulta de endereço por CEP (retorno único);
- Consulta de endereços por cidade, com limite de resultados;
- Health check com verificação da conexão com o banco;
- Carga automática dos dados na inicialização: a tabela é criada
  (se não existir) e o CSV é importado (se o banco estiver vazio);
- Tratamento global de erros: falhas internas de banco retornam
  mensagens genéricas; os detalhes técnicos ficam apenas nos logs.

Fonte dos dados: [CSV público de CEPs (2019)](https://raw.githubusercontent.com/miltonhit/miltonhit/main/public-assets/cep-20190602.csv),
baixado durante a inicialização.

## Stack

| Tecnologia | Uso |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Framework da API |
| [Uvicorn](https://www.uvicorn.org/) | Servidor ASGI |
| MySQL | Armazenamento dos endereços |
| mysql-connector-python | Driver assíncrono com pool de conexões |
| Pydantic | Modelos de request/response |
| httpx | Download do CSV de CEPs |
| Poetry | Gerenciamento de dependências |
| pytest / pytest-asyncio | Testes automatizados |

## Arquitetura

A aplicação segue uma arquitetura em camadas, com dependências sempre
apontando para dentro (abstrações definidas por interfaces ABC):

```
Controller → Service → Repository → Database
```

- **Controller** (`controller/`): rotas FastAPI; converte HTTP em
  chamadas de serviço. Sem regras de negócio;
- **Service** (`service/`): regras de negócio (validações, quando
  lançar "não encontrado", fluxo de importação do CSV);
- **Repository** (`repository/`): apenas acesso a dados; monta as
  queries e devolve modelos;
- **Database** (`database.py`): pool assíncrono de conexões MySQL,
  criado de forma lazy e compartilhado;
- **Interfaces** (`interfaces.py`): contratos (`IDatabaseConnection`,
  `ICorreiosRepository`, `ISetupRepository`) que permitem trocar
  implementações sem afetar as camadas superiores;
- **Container** (`container.py`): singleton que centraliza e injeta as
  dependências.

### Estrutura do projeto

```
src/correios_cep/
├── main.py                     # App FastAPI, lifespan e handlers
├── container.py                # Injeção de dependências (singleton)
├── database.py                 # Pool assíncrono de conexões MySQL
├── interfaces.py               # Contratos (ABC) das camadas
├── exceptions.py               # Exceções de domínio → status HTTP
├── addresses.sql               # DDL da tabela (CREATE TABLE IF NOT EXISTS)
├── model/
│   └── address.py              # Modelo Pydantic Address
├── controller/
│   └── correios_controller.py  # Rotas /zip e /city
├── service/
│   ├── correios_service.py     # Regras das consultas de endereço
│   └── csvfile_service.py      # Download, gravação e importação do CSV
└── repository/
    ├── correios_repository.py  # Consultas de endereço
    └── setup_repository.py     # Criação da tabela e carga de dados
tests/                          # Testes unitários e de integração
```

## Requisitos

- Python 3.13+
- Poetry
- MySQL 8+ com `local_infile` habilitado (necessário para o
  `LOAD DATA LOCAL INFILE` da carga do CSV)

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
HOST=localhost
USER=seu_usuario
PASSWORD=sua_senha
DATABASE=correios
```

## Instalação e execução

```bash
poetry install
poetry run uvicorn src.correios_cep.main:app --reload
```

Na inicialização (lifespan), a aplicação:

1. Cria a tabela `addresses` executando `addresses.sql`
   (`CREATE TABLE IF NOT EXISTS`, idempotente);
2. Verifica se já existem CEPs no banco;
3. Se o banco estiver vazio, baixa o CSV público, grava um arquivo
   temporário e importa via `LOAD DATA LOCAL INFILE`.

## Endpoints

### `GET /zip/{zipcode}`

Retorna o endereço correspondente ao CEP (8 dígitos).

```json
{
  "state": "MG",
  "city": "Carangola",
  "neighborhood": "Alvorada",
  "zipcode": "36803000",
  "street": ""
}
```

### `GET /city/{city}?limit=100`

Retorna os endereços da cidade informada.

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `city` | path (str) | — | Nome da cidade |
| `limit` | query (int) | 100 | Máximo de resultados (1 a 500) |

Resposta: lista de objetos `Address` (mesmo formato do endpoint
anterior).

### `GET /health_check`

Verifica a aplicação e a conexão com o banco.

```json
{ "message": "OK", "status": "healthy", "database": "connected" }
```

### Códigos de erro

| Status | Situação | Exemplo de `detail` |
|---|---|---|
| 400 | CEP ou cidade vazios | `"CEP não pode ser vazio"` |
| 400 | `limit` fora da faixa (1–500) | `"Limite não pode ser maior que 500"` |
| 404 | CEP ou cidade sem resultado | `"CEP 00000000 não encontrado"` |
| 422 | `limit` com valor não numérico | erros de validação (padrão FastAPI) |
| 500 | Falha de banco de dados | `"Erro ao executar consulta"` (genérica) |
| 503 | Banco indisponível no health check | `"Database unavailable"` |

Erros inesperados do driver (host, usuário, SQL etc.) são registrados
nos logs via `logging` e **não** são expostos na resposta.

## Testes

```bash
poetry run pytest
```

- **Testes unitários** (`CSVFileService`, `SetupRepository`) rodam sem
  banco: usam fakes e `tmp_path`;
- **Testes de integração** (`tests/test_controller.py`) exigem o
  `.env` configurado e um MySQL acessível com os dados carregados —
  sem isso, falham com 500/503.

