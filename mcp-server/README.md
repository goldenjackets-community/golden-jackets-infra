# Golden Jackets MCP Server

MCP server local para operações da comunidade Golden Jackets via Kiro CLI.

## Tools disponíveis

| Tool | Descrição | Permissão |
|------|-----------|-----------|
| `list-members` | Lista membros do Lounge (Cognito) | leitura |
| `list-chapters` | Lista chapters disponíveis | leitura |
| `chapter-status` | Status CloudFront/S3 de todos os chapters | leitura |
| `invalidate-cache` | Invalida cache CloudFront de um chapter | escrita |
| `suggest-topic` | Sugere tópico de artigo (SNS) | escrita |

## Setup

### Pré-requisitos
- Python 3.9+
- boto3 instalado (`pip install boto3`)
- AWS profile `gj` configurado

### Configurar no Kiro CLI

Adicionar ao `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "goldenjackets": {
      "command": "python3",
      "args": ["/home/gulias/golden-jackets-infra/mcp-server/server.py"],
      "env": {
        "AWS_PROFILE": "gj",
        "AWS_DEFAULT_REGION": "us-east-1"
      }
    }
  }
}
```

Reiniciar Kiro CLI para ativar.

## Uso

Após ativação, basta conversar normalmente:
- "lista os membros do brazil"
- "qual o status dos chapters?"
- "invalida o cache do poland"
- "sugere o tópico X para artigo"
