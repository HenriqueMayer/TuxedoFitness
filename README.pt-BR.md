# Tuxedo Fitness

**Versão 0.2.0** · [English](README.md) · [Documentação](docs/README.md) · [Prévia da interface](preview/pt-br/index.html)

Aplicação local de acompanhamento e planejamento de treinos da família Tuxedo. Conecte o Hevy uma vez, consulte seu histórico, analise sua evolução e gere prompts completos para a LLM que preferir. Confira uma proposta JSON antes de criar ou atualizar rotinas no Hevy.

- Credencial Hevy criptografada por usuário, preservada após logout e reinício.
- Histórico completo, rotinas por pasta, catálogo com busca bilíngue e exportações CSV/JSON.
- Análises de frequência, carga, RPE, volume, distribuição, duração e modalidades, com preferências salvas.
- Perfil opcional e gerações de prompt imutáveis, com os dados originais do Hevy.
- Criação/atualização de várias rotinas com validação, comparação, confirmação de uso único e resultados por operação.
- EN/PT-BR, temas claro/escuro e preferências independentes de unidade, formato de data e fuso.

Nutrição, medidas corporais, edição de treinos concluídos e chat integrado ficam fora desta versão. O Fitness não envia seus dados a uma LLM. A API do Hevy exige Hevy Pro.

## Instalação

Requisitos: Python 3.12+ e [uv](https://docs.astral.sh/uv/). Node é necessário apenas para reconstruir assets e executar testes de navegador.

```bash
uv sync --locked
uv run python scripts/init_local.py
uv run python manage.py migrate
uv run python manage.py runserver
```

Acesse <http://127.0.0.1:8000/>, crie sua conta e salve a chave na tela **Conexão Hevy**. A primeira sincronização importa todo o histórico. As seguintes atualizam treinos e rotinas após 15 minutos de uso e o catálogo a cada 24 horas. O botão do cabeçalho permite atualizar manualmente, inclusive sem JavaScript.

**A versão 0.2.0 exige banco novo.** Não há migração suportada dos dados 0.1.x. Preserve a instalação anterior e siga o [procedimento operacional](docs/operations.md). O diretório padrão é `var/private/v020`.

Guarde backups do SQLite e das chaves de criptografia da instalação separadamente. Desconectar remove a credencial e mantém os registros locais. Os prompts podem conter informações pessoais: o compartilhamento ocorre quando você os copia para a ferramenta escolhida.

## Desenvolvimento

O contrato de família segue o Finance no commit `90cfe53`. Veja [paridade](docs/tuxedo-parity.md), [contribuição](CONTRIBUTING.md) e [operação](docs/operations.md). Código e documentação técnica usam inglês. O preview contém somente dados sintéticos.

Licença [PolyForm Noncommercial 1.0.0](LICENSE).
