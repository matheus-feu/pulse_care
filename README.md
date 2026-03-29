<p align="center">
  <h1 align="center">🏥 PulseCare API</h1>
  <p align="center">
    REST API para gerenciamento de clínicas e consultórios médicos.<br/>
    Controle de pacientes, agendamentos, prontuários e equipe de profissionais.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/django-6.0-green?logo=django&logoColor=white" alt="Django 6.0" />
  <img src="https://img.shields.io/badge/DRF-3.17-red?logo=django&logoColor=white" alt="DRF 3.17" />
  <img src="https://img.shields.io/badge/celery-5.6-green?logo=celery&logoColor=white" alt="Celery 5.6" />
  <img src="https://img.shields.io/badge/postgres-16-blue?logo=postgresql&logoColor=white" alt="PostgreSQL 16" />
  <img src="https://img.shields.io/badge/redis-7-red?logo=redis&logoColor=white" alt="Redis 7" />
  <img src="https://img.shields.io/badge/docker-compose-blue?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
</p>

---

## 📑 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Stack & Tecnologias](#-stack--tecnologias)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação & Execução](#-instalação--execução)
  - [Com Docker (recomendado)](#-com-docker-recomendado)
  - [Sem Docker (local)](#-sem-docker-local)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Endpoints da API](#-endpoints-da-api)
  - [Autenticação (JWT)](#autenticação-jwt)
  - [Usuários](#usuários)
  - [Pacientes](#pacientes)
  - [Agendamentos](#agendamentos)
  - [Prontuários](#prontuários)
- [Documentação Interativa](#-documentação-interativa)
- [Background Tasks (Celery)](#-background-tasks-celery)
- [Observabilidade (Elastic APM)](#-observabilidade-elastic-apm)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Licença](#-licença)

---

## 💡 Sobre o Projeto

**PulseCare** é uma API REST completa para gestão de saúde, projetada para clínicas e consultórios. O sistema permite:

- **Gerenciar equipe** — médicos, enfermeiros, recepcionistas e administradores com controle de acesso baseado em papéis (RBAC).
- **Cadastrar pacientes** — dados pessoais, contato, endereço, informações médicas, convênio e contato de emergência.
- **Agendar consultas** — múltiplos tipos (consulta, retorno, exame, procedimento, emergência, telemedicina) com controle de status.
- **Registrar prontuários** — avaliação clínica, sinais vitais, diagnóstico (CID-10), prescrições e upload de anexos (exames, imagens, etc.).
- **Notificações automáticas** — lembretes de consulta e e-mails de boas-vindas via Celery.
- **Monitoramento** — logs estruturados, request tracing e Elastic APM integrado.

---

## 🛠 Stack & Tecnologias

| Camada            | Tecnologia                                                                 |
|-------------------|---------------------------------------------------------------------------|
| **Linguagem**     | Python 3.13                                                               |
| **Framework**     | Django 6.0 + Django REST Framework 3.17                                   |
| **Autenticação**  | JWT (Simple JWT) — access token (8h) + refresh token (7d)                 |
| **Banco de Dados**| PostgreSQL 16                                                             |
| **Cache/Broker**  | Redis 7                                                                   |
| **Task Queue**    | Celery 5.6 + Celery Beat (agendamento periódico)                         |
| **Documentação**  | drf-spectacular (OpenAPI 3.0) — Swagger UI + ReDoc                        |
| **Observabilidade**| Elastic APM + Elasticsearch 8.13 + Kibana                               |
| **Filtros**       | django-filter                                                             |
| **CORS**          | django-cors-headers                                                       |
| **Containerização**| Docker + Docker Compose                                                  |

---

## 🏗 Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Client /  │────▶│   Django     │────▶│ PostgreSQL │
│   Frontend  │◀────│   REST API   │◀────│   (db)     │
└─────────────┘     └──────┬───────┘     └────────────┘
                           │
                    ┌──────┴───────┐
                    │    Redis     │
                    │   (broker)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │                         │
      ┌───────▼──────┐         ┌───────▼───────┐
      │ Celery Worker│         │ Celery Beat   │
      │ (async tasks)│         │ (scheduler)   │
      └──────────────┘         └───────────────┘
                           │
                    ┌──────▼───────┐
                    │  Elastic APM │
                    │  Kibana      │
                    └──────────────┘
```

---

## ✅ Pré-requisitos

- **Docker** e **Docker Compose** (recomendado) **ou**
- Python 3.13+, PostgreSQL 16, Redis 7

---

## 🚀 Instalação & Execução

### 🐳 Com Docker (recomendado)

**1. Clone o repositório:**

```bash
git clone https://github.com/seu-usuario/pulse_care.git
cd pulse_care
```

**2. Crie o arquivo `.env`:**

```bash
cp .env.example .env
# Edite as variáveis conforme necessário (veja a seção abaixo)
```

**3. Suba todos os serviços:**

```bash
docker compose up -d --build
```

Isso iniciará:

| Serviço              | Porta  | Descrição                          |
|----------------------|--------|------------------------------------|
| `pulse_care_web`     | 8000   | API Django                         |
| `pulse_care_db`      | 5432   | PostgreSQL                         |
| `pulse_care_redis`   | 6379   | Redis (broker do Celery)           |
| `pulse_care_celery_worker` | — | Worker para tasks assíncronas |
| `pulse_care_celery_beat`   | — | Scheduler para tasks periódicas |
| `pulse_care_elasticsearch` | 9200 | Elasticsearch                  |
| `pulse_care_kibana`  | 5601   | Kibana (dashboard de logs/APM)     |
| `pulse_care_apm_server` | 8200 | APM Server                       |

**4. Execute as migrações e crie um superusuário:**

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

**5. Acesse:**

- API: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Admin: http://localhost:8000/admin/
- Kibana: http://localhost:5601/
- Health Check: http://localhost:8000/health/

---

### 💻 Sem Docker (local)

**1. Crie e ative um ambiente virtual:**

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

**2. Instale as dependências:**

```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente** (veja seção abaixo) e garanta que PostgreSQL e Redis estejam rodando.

**4. Execute migrações e inicie o servidor:**

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**5. Em terminais separados, inicie o Celery:**

```bash
# Worker
celery -A core worker --loglevel=info

# Beat (scheduler)
celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 🔐 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Django
SECRET_KEY=sua-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
DB_ENGINE=django.db.backends.postgresql
DB_NAME=pulse_care
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# JWT
JWT_ACCESS_HOURS=8
JWT_REFRESH_DAYS=7

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500

# E-mail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=PulseCare <noreply@pulsecare.com>

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Elastic APM
APM_SERVICE_NAME=pulse-care-api
APM_ENVIRONMENT=development
APM_SERVER_URL=http://localhost:8200
APM_SECRET_TOKEN=
APM_SAMPLE_RATE=1.0

# Appointments
APPOINTMENT_REMINDER_HOURS_BEFORE=24

# Logging
LOG_LEVEL=INFO
CELERY_LOG_LEVEL=INFO

# Pagination
PAGE_SIZE=20
```

---

## 📡 Endpoints da API

Base URL: `http://localhost:8000/api/`

### Autenticação (JWT)

| Método | Endpoint                  | Descrição                                  |
|--------|---------------------------|--------------------------------------------|
| POST   | `/api/auth/token/`        | Obter tokens (access + refresh) via email/senha |
| POST   | `/api/auth/token/refresh/`| Renovar access token com refresh token     |

**Exemplo de autenticação:**

```bash
# Obter tokens
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@pulsecare.com", "password": "sua-senha"}'

# Resposta
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}

# Usar token nas requisições
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..." \
  http://localhost:8000/api/users/me/
```

---

### Contas (Accounts)

| Método | Endpoint                                | Descrição                          | Permissão |
|--------|-----------------------------------------|------------------------------------|-----------|
| POST   | `/api/accounts/register/`               | Criar nova conta (auto-cadastro)   | Público   |
| POST   | `/api/accounts/password-reset/`         | Solicitar redefinição de senha     | Público   |
| POST   | `/api/accounts/password-reset/confirm/` | Confirmar nova senha (uid + token) | Público   |

**Registro:**

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "joao.silva",
    "email": "joao@email.com",
    "first_name": "João",
    "last_name": "Silva",
    "phone": "(11) 99999-0000",
    "password": "SenhaSegura123!",
    "confirm_password": "SenhaSegura123!"
  }'
```

> Novos usuários recebem o role padrão `receptionist`. Um admin pode promover depois via `PUT /api/users/{id}/`.

**Recuperação de senha:**

```bash
# 1. Solicitar reset (envia e-mail com uid + token)
curl -X POST http://localhost:8000/api/accounts/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "joao@email.com"}'

# 2. Confirmar nova senha
curl -X POST http://localhost:8000/api/accounts/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "Mg",
    "token": "c5v4k2-abc...",
    "new_password": "NovaSenha456!",
    "confirm_new_password": "NovaSenha456!"
  }'
```

---

### Usuários

| Método | Endpoint                       | Descrição                          | Permissão       |
|--------|--------------------------------|------------------------------------|-----------------|
| GET    | `/api/users/`                  | Listar usuários ativos             | Autenticado     |
| POST   | `/api/users/`                  | Criar novo usuário                 | Admin           |
| GET    | `/api/users/{id}/`             | Detalhes de um usuário             | Autenticado     |
| PUT    | `/api/users/{id}/`             | Atualizar usuário                  | Autenticado     |
| PATCH  | `/api/users/{id}/`             | Atualização parcial                | Autenticado     |
| DELETE | `/api/users/{id}/`             | Desativar usuário (soft delete)    | Admin           |
| GET    | `/api/users/me/`               | Perfil do usuário autenticado      | Autenticado     |
| PATCH  | `/api/users/me/update/`        | Atualizar próprio perfil           | Autenticado     |
| POST   | `/api/users/me/change-password/` | Alterar senha                    | Autenticado     |

**Roles disponíveis:** `admin`, `doctor`, `nurse`, `receptionist`

**Filtros:** `?role=doctor`, `?is_active=true`, `?is_staff=true`  
**Busca:** `?search=nome ou email`  
**Ordenação:** `?ordering=first_name`, `-created_at`, `role`

---

### Pacientes

| Método | Endpoint                         | Descrição                          | Permissão   |
|--------|----------------------------------|------------------------------------|-------------|
| GET    | `/api/patients/`                 | Listar pacientes ativos            | Autenticado |
| POST   | `/api/patients/`                 | Cadastrar novo paciente            | Autenticado |
| GET    | `/api/patients/{id}/`            | Detalhes de um paciente            | Autenticado |
| PUT    | `/api/patients/{id}/`            | Atualizar paciente                 | Autenticado |
| PATCH  | `/api/patients/{id}/`            | Atualização parcial                | Autenticado |
| DELETE | `/api/patients/{id}/`            | Desativar paciente (soft delete)   | Autenticado |
| GET    | `/api/patients/{id}/history/`    | Histórico clínico completo         | Autenticado |

**Filtros:** CPF, gênero, tipo sanguíneo, cidade, estado, convênio, etc.  
**Busca:** `?search=nome, cpf, email ou telefone`  
**Ordenação:** `?ordering=last_name`, `date_of_birth`, `created_at`  
**Parâmetros extras:** `?show_inactive=true` para incluir inativos

---

### Agendamentos

| Método | Endpoint                              | Descrição                           | Permissão   |
|--------|---------------------------------------|-------------------------------------|-------------|
| GET    | `/api/appointments/`                  | Listar agendamentos                 | Autenticado |
| POST   | `/api/appointments/`                  | Criar novo agendamento              | Autenticado |
| GET    | `/api/appointments/{id}/`             | Detalhes de um agendamento          | Autenticado |
| PUT    | `/api/appointments/{id}/`             | Atualizar agendamento               | Autenticado |
| PATCH  | `/api/appointments/{id}/`             | Atualização parcial                 | Autenticado |
| DELETE | `/api/appointments/{id}/`             | Excluir agendamento                 | Autenticado |
| PATCH  | `/api/appointments/{id}/status/`      | Atualizar status do agendamento     | Autenticado |
| GET    | `/api/appointments/today/`            | Agendamentos de hoje                | Autenticado |
| GET    | `/api/appointments/my/`               | Agendamentos do médico autenticado  | Autenticado |

**Status:** `scheduled` → `confirmed` → `in_progress` → `completed` | `cancelled` | `no_show`  
**Tipos:** `consultation`, `follow_up`, `exam`, `procedure`, `emergency`, `telemedicine`  
**Filtros:** status, médico, paciente, tipo, intervalo de datas  
**Busca:** `?search=nome do paciente, cpf ou motivo`

---

### Prontuários

| Método | Endpoint                                     | Descrição                          | Permissão   |
|--------|----------------------------------------------|------------------------------------|-------------|
| GET    | `/api/records/`                              | Listar prontuários                 | Autenticado |
| POST   | `/api/records/`                              | Criar prontuário                   | Autenticado |
| GET    | `/api/records/{id}/`                         | Detalhes de um prontuário          | Autenticado |
| PUT    | `/api/records/{id}/`                         | Atualizar prontuário               | Autenticado |
| PATCH  | `/api/records/{id}/`                         | Atualização parcial                | Autenticado |
| DELETE | `/api/records/{id}/`                         | Excluir prontuário                 | Autenticado |
| POST   | `/api/records/{id}/attachments/`             | Upload de anexo (multipart)        | Autenticado |
| GET    | `/api/records/{id}/attachments/`             | Listar anexos do prontuário        | Autenticado |
| DELETE | `/api/records/attachments/{id}/`             | Excluir um anexo específico        | Autenticado |

**Inclui:** queixa principal, história da doença, exame físico, sinais vitais (PA, FC, FR, temperatura, SpO2, peso, altura, IMC calculado), diagnóstico, CID-10, prescrição, plano de tratamento e encaminhamentos.

**Tipos de anexo:** `exam_result`, `image`, `prescription`, `referral`, `other`  
**Filtros:** paciente, médico, CID-10, intervalo de datas  
**Busca:** `?search=nome do paciente, cpf, diagnóstico ou queixa`

---

## 📖 Documentação Interativa

A API possui documentação automática gerada a partir do código com **drf-spectacular** (OpenAPI 3.0):

| Interface   | URL                                    | Descrição                              |
|-------------|----------------------------------------|----------------------------------------|
| Swagger UI  | http://localhost:8000/api/docs/        | Documentação interativa (testar endpoints) |
| ReDoc       | http://localhost:8000/api/redoc/       | Documentação em formato mais visual    |
| Schema JSON | http://localhost:8000/api/schema/      | Schema OpenAPI 3.0 em JSON             |

> 💡 **Dica:** No Swagger UI, clique em **"Authorize"** e insira `Bearer <seu_access_token>` para testar endpoints autenticados.

---

## ⚙ Background Tasks (Celery)

O PulseCare utiliza **Celery** com **Redis** como broker para processar tarefas assíncronas:

| Task                                     | Trigger                         | Descrição                                |
|------------------------------------------|---------------------------------|------------------------------------------|
| `users.send_welcome_email`               | Criação de usuário (signal)     | Envia e-mail de boas-vindas ao novo membro da equipe |
| `appointments.send_appointment_reminder` | Criação de agendamento (signal) | Envia lembrete por e-mail ao paciente N horas antes da consulta |
| `records.notify_doctor_record_created`   | Criação de prontuário (signal)  | Notifica o médico responsável sobre um novo prontuário |

- **Celery Beat** gerencia tarefas periódicas via `django-celery-beat` (configurável pelo Django Admin).
- **Resultados** das tasks são armazenados no banco via `django-celery-results`.
- Todas as tasks possuem **retry automático** (até 3 tentativas) em caso de falha.

---

## 📊 Observabilidade (Elastic APM)

O projeto integra a stack **Elastic Observability** para monitoramento em tempo real:

- **Elastic APM** — tracing de requisições HTTP e tasks do Celery
- **Elasticsearch** — armazenamento de logs e métricas
- **Kibana** (http://localhost:5601) — dashboards de performance, erros e logs

**Middlewares customizados incluídos:**

- `RequestLoggingMiddleware` — loga cada request com UUID, método, path, status, duração (ms), usuário e IP
- `HealthCheckMiddleware` — endpoint `GET /health/` retorna `{"status": "ok"}` sem autenticação (ideal para probes de container/load balancer)

---

## 📄 Licença

Este projeto está licenciado sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  Feito com muito esfoço — <strong>Matheus Feu</strong>
</p>

