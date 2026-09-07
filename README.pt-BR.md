[English](README.md) | [Português (Brasil)](README.pt-BR.md)

<p align="center">
  <img src="static/brand/tuxedo-fitness-emblem.png" width="144" alt="Tuxedo Fitness">
</p>
<h1 align="center">Tuxedo Fitness</h1>
<p align="center">
  <a href="https://github.com/HenriqueMayer/TuxedoFitness/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/HenriqueMayer/TuxedoFitness/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=101E18&amp;color=176B52" alt="CI status"></a>
  <img src="https://img.shields.io/badge/version-0.2.0-B88A59?style=for-the-badge&amp;labelColor=101E18" alt="Version 0.2.0">
  <img src="https://img.shields.io/badge/Python-3.12-176B52?style=for-the-badge&amp;labelColor=101E18" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Django-6.0-1A2E26?style=for-the-badge&amp;labelColor=101E18" alt="Django 6.0">
  <img src="https://img.shields.io/badge/UI-EN%20%7C%20PT--BR-B88A59?style=for-the-badge&amp;labelColor=101E18" alt="EN / PT-BR">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-PolyForm%20Noncommercial-7C5C13?style=for-the-badge&amp;labelColor=101E18" alt="PolyForm Noncommercial"></a>
</p>

O Tuxedo Fitness é uma aplicação local para consultar o histórico do Hevy,
acompanhar rotinas, comparar indicadores de exercícios e gerar prompts para a
LLM de sua escolha. Os registros ficam em um banco SQLite sob seu controle.
A aplicação não envia seus dados automaticamente para uma LLM. O acesso à API
do Hevy exige Hevy Pro.

## Prévia da interface

<table><tr><td width="96" align="center"><img src="static/brand/tuxedo-fitness-emblem-128.png" width="72" alt="Emblema Fitness"></td><td><strong>Conheça a interface antes de instalar.</strong><br>Visão geral, análises, histórico, rotinas, exercícios e geração de prompts.<br><br><a href="preview/pt-br/index.html"><strong>Abrir a prévia em português →</strong></a> · <a href="preview/index.html">English</a></td></tr></table>

A prévia usa capturas sintéticas e funciona por arquivos HTML locais ou servidor
estático. Não possui conta, backend ou persistência. A hospedagem está descrita
na [configuração do Pages](docs/operations.md#interface-preview-on-github-pages).

## Instalação rápida

Requisitos: Python 3.12+ e [uv](https://docs.astral.sh/uv/).
Para uma **instalação nova**:

```bash
git clone https://github.com/HenriqueMayer/TuxedoFitness.git
cd TuxedoFitness
uv sync --locked
uv run python scripts/init_local.py
uv run python manage.py migrate
uv run python manage.py runserver
```

Abra [a aplicação](http://127.0.0.1:8000/), crie sua conta e salve sua chave em
**Conexão Hevy**. A sincronização importa catálogo, rotinas e histórico. A chave
é criptografada por conta e preservada após reiniciar a aplicação.

Para uma **instalação 0.2.0 existente**, faça backup do SQLite e das chaves,
preserve a configuração e o banco e atualize com:

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py translate_exercises
uv run python manage.py runserver
```

Esta revisão não exige reiniciar o banco. Somente a transição antiga
**0.1.x → 0.2.0** exige o [procedimento separado](docs/operations.md).
Node é necessário apenas no desenvolvimento; os assets compilados estão incluídos.

## Funcionalidades

| Área | Recursos |
|---|---|
| Visão geral | Atividade, séries, distribuição de esforço e evolução do exercício selecionado. |
| Análises | Seis tópicos, comparação por indicador, recordes datados, metas semanais e distribuição por músculo principal. |
| Histórico | Histórico completo sincronizado, filtros por exercício/série e exportações CSV/JSON. |
| Rotinas | Pastas, prescrições e propostas de criação/atualização em lote com confirmação de uso único. |
| Exercícios | Catálogo PT-BR versionado com 451 exercícios padrão, busca bilíngue e favoritos. Nomes personalizados são preservados. |
| Prompts | Perfil opcional, seleção do histórico, dados originais e gerações salvas imutáveis. |
| Interface | EN/PT-BR, temas claro/escuro, gráficos por teclado/toque e alternativas sem JavaScript. |
| Preferências | Unidades de massa/distância, datas, fuso, ordem dos painéis e meta semanal independentes. |

Os gráficos descrevem o treino registrado. O 1RM é estimado; assistência, RPE,
volume e modalidades diferentes não são tratados como pontuações equivalentes.

## Tecnologia

| Camada | Tecnologia |
|---|---|
| Backend | Python, Django e autenticação nativa |
| Frontend | Templates Django, Tailwind CSS, HTMX, JavaScript e SVG calculado no servidor |
| Armazenamento | SQLite WAL e chaves de criptografia administradas separadamente |
| Ferramentas | Lockfiles uv/npm, Node 24 no desenvolvimento e testes Playwright isolados |

## Configuração e propriedade dos dados

A configuração vem do `.env` ou das variáveis do processo, que têm prioridade.
`SECRET_KEY` e `HEVY_ENCRYPTION_KEYS` têm funções distintas; `TUXEDO_DATA_DIR`
define o diretório de dados. `ALLOW_SIGNUPS=False` fecha novos cadastros e
preserva o login. Consulte [operação](docs/operations.md).

Guarde backups do banco e das chaves separadamente. Desconectar o Hevy remove a
credencial e mantém os registros locais. Compartilhar prompts é uma ação do
usuário. Traduções não alteram os dados originais nem os títulos nas exportações.

## Desenvolvimento

Veja [CONTRIBUTING](CONTRIBUTING.md) para instalação, cobertura e traduções.
Use Node 24 e o lockfile da raiz:

```bash
npm ci
npm run build
npm run test:e2e
npm run test:preview
```

Os testes de navegador usam bancos sintéticos descartáveis. O Fitness é
instalável de forma independente e segue o [contrato Tuxedo](docs/tuxedo-parity.md).

## Documentação

- [Índice](docs/README.md) e [requisitos do produto](docs/product-requirements.md)
- [Arquitetura](docs/architecture.md) e [modelo de dados](docs/data-model.md)
- [Análises](docs/analytics.md) e [frontend](docs/frontend.md)
- [Integração Hevy](docs/hevy-integration.md) e [planejamento](docs/planning.md)
- [Operação](docs/operations.md), [testes](docs/testing.md) e [desempenho](docs/performance.md)
- [Auditoria do repositório](docs/repository-audit.md) e [histórico de alterações](CHANGELOG.md)

Código e documentação técnica usam inglês. Os dois READMEs devem ser atualizados juntos.

## Contribuição e licença

Leia [CONTRIBUTING](CONTRIBUTING.md) antes de propor alterações.
Copyright © 2026 Henrique Mayer. Licença
[PolyForm Noncommercial 1.0.0](LICENSE).
