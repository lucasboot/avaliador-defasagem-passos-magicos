# Classificador de Risco de Defasagem Escolar

API FastAPI para classificação de risco de defasagem escolar, desenvolvida para o Datathon da Passos Mágicos. Utiliza um modelo LLM fine-tuned da OpenAI para classificar casos de alunos em uma das três categorias: **em_fase**, **moderada** ou **severa**.

## Visão Geral

A solução recebe um texto em linguagem natural descrevendo o aluno (idade, fase na associação, indicadores como IDA, IEG, IAA, IPS, IPP, IPV, IAN, INDE, etc.) e retorna a classificação de risco de defasagem. A resposta é normalizada e validada para garantir que apenas uma das três classes seja retornada. Opcionalmente, uma segunda chamada a um modelo comum da OpenAI (ex.: gpt-4o-mini) gera uma explicação breve e humanizada da classificação.

## Arquitetura

```
project/
  app/
    main.py              # Aplicação FastAPI
    config.py            # Configurações via variáveis de ambiente
    schemas.py           # Contratos Pydantic
    routes/
      predict.py         # POST /predict
      pages.py           # GET / (home)
      eval.py            # POST /eval
      health.py          # GET /health
    services/
      openai_client.py   # Cliente OpenAI
      classifier.py      # Lógica de classificação
      explainer.py       # Geração de explicação humanizada
      evaluator.py       # Avaliação sobre dataset
      normalizer.py      # Normalização da saída
    templates/
      home.html          # Interface web
    static/
      style.css
      app.js
    utils/
      logging.py         # Logging estruturado JSON
      errors.py          # Exceções de domínio
  tests/
  data/processed/
    test.jsonl           # Dataset para avaliação
```

## Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | `sk-...` |
| `OPENAI_MODEL` | Nome do modelo fine-tuned | `ft:gpt-4o-mini:...` |
| `OPENAI_EXPLANATION_MODEL` | Modelo para gerar explicação humanizada | `gpt-4o-mini` |
| `APP_ENV` | Ambiente (development/production) | `development` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `EVAL_DATASET_PATH` | Caminho do arquivo test.jsonl | `data/processed/test.jsonl` |

## Instalação

```bash
pip install -r requirements.txt
```

Ou com ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Containerização (Docker)

Para facilitar o setup em qualquer máquina, você pode rodar tudo com Docker.

### Pré-requisitos

- Docker
- Docker Compose (comando `docker compose`)

### Setup inicial

1. Copie o arquivo de exemplo de variáveis:

```bash
cp .env.example .env
```

2. Preencha no `.env` pelo menos:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL`

### Opção A - Docker Compose (recomendada)

```bash
docker compose up --build
```

Para parar:

```bash
docker compose down
```

### Opção B - Docker puro

```bash
docker build -t classificador-defasagem .
docker run -p 8000:8000 --env-file .env classificador-defasagem
```

### Acesso

- Interface web: http://localhost:8000/
- Documentação Swagger: http://localhost:8000/docs

Observação: o arquivo `.env` deve existir no host e não é copiado para dentro da imagem.

## Como Rodar Localmente

1. Configure as variáveis de ambiente (crie um arquivo `.env` se desejar):

```bash
export OPENAI_API_KEY="sua-chave"
export OPENAI_MODEL="ft:gpt-4o-mini:..."
```

2. Inicie o servidor:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Acesse:
   - Interface web: http://localhost:8000/
   - Documentação Swagger: http://localhost:8000/docs

## Como Testar

```bash
pytest tests/ -v
```

Com Docker (sem subir a API):

```bash
docker compose run --rm app pytest tests/ -v
```

Com cobertura:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

Com cobertura via Docker:

```bash
docker compose run --rm -e PYTHONPATH=/app app python -m pytest tests --cov=app --cov-report=term-missing
```

Cobertura total atual da suíte de testes: **94%**.

## CI/CD

O projeto possui esteira de CI em `.github/workflows/deploy.yml` para validar qualidade do codigo a cada `push` na branch `main`.

### O que a esteira executa

1. Checkout do codigo.
2. Setup do Python.
3. Instalacao de dependencias (`requirements.txt`).
4. Validacao de import da aplicacao FastAPI.
5. Testes com `pytest` e cobertura minima de `80%` (`--cov-fail-under=80`).
6. Health check no endpoint `/health` via `TestClient`.
7. Avaliação offline com `python scripts/run_eval.py`.
8. Avaliação do endpoint `/predict` com `python scripts/eval_predict_endpoint.py` (falha se `accuracy < 0.80`).

### Como acontece o deploy no Railway

- O deploy e feito pelo proprio Railway, pois o repositorio esta conectado na branch `main`.
- Com a opcao **Wait for CI** ativada no Railway, o deploy so avanca quando o GitHub Actions finalizar com sucesso.

### Segredos usados na esteira

Para as etapas de avaliação do modelo no CI, configure no GitHub:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EXPLANATION_MODEL` (opcional, usado apenas em chamadas com explicação)

### Como acompanhar a execucao no GitHub Actions

1. Acesse a aba **Actions** do repositorio no GitHub.
2. Abra o workflow **CI FastAPI**.
3. Clique na execucao do commit para ver logs de cada etapa.

### Como verificar o deploy no Railway

1. No Railway, abra o projeto e o servico implantado.
2. Confira os logs da ultima implantacao.
3. Valide o endpoint de saude da aplicacao publicada:

```bash
curl https://<seu-dominio-railway>/health
```

## Como Chamar a API

### Predição (POST /predict)

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"student_text": "Aluno de 13 anos que está há 2 anos na associação. Está na fase 3 da associação. O nível ideal para sua idade seria Nível 4 (9o ano). Possui desempenho acadêmico IDA de 6.9, engajamento IEG de 8.6..."}'
```

Resposta:

```json
{
  "prediction": "moderada",
  "model": "ft:gpt-4o-mini:...",
  "raw_output": "moderada",
  "normalized": true,
  "explanation": "O aluno apresenta indicadores que sugerem uma defasagem moderada..."
}
```

O campo `explanation` é gerado por um modelo comum (ex.: gpt-4o-mini) e pode ser desativado passando `"include_explanation": false` no body.

### Health (GET /health)

```bash
curl http://localhost:8000/health
```

### Avaliação (POST /eval)

Executa a avaliação sobre o arquivo `data/processed/test.jsonl`:

```bash
curl -X POST http://localhost:8000/eval
```

Para rodar a avaliação direto no container (sem chamar endpoint HTTP):

```bash
docker compose run --rm app python scripts/run_eval.py
```

Resposta:

```json
{
  "total": 72,
  "accuracy": 0.85,
  "macro_f1": 0.84,
  "f1_per_class": {"em_fase": 0.88, "moderada": 0.82, "severa": 0.83},
  "confusion_matrix": [[...], [...], [...]],
  "errors": [{"index": 1, "expected": "moderada", "predicted": "em_fase"}, ...]
}
```

## Interface Web

A rota `GET /` renderiza uma página com:

- Título e descrição do projeto
- Textarea para digitar o caso do aluno
- Botão "Classificar"
- Área para exibir a classe retornada em destaque
- Resposta bruta do modelo (expansível)
- Mensagens de erro em caso de falha

A classificação é feita via `fetch` sem recarregar a página.

## Licença

Projeto acadêmico - Datathon Passos Mágicos.
