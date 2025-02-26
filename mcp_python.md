# Guia de Servidores MCP para Ferramentas (Tools) em Python

## 1. O que é um Servidor MCP focado em Tools?

Um servidor MCP cria uma ponte entre os LLMs (Large Language Models) e o mundo externo. Enquanto os LLMs podem gerar texto e código, eles não conseguem interagir diretamente com sistemas externos - é aí que entram os servidores MCP de Tools.

**Tools são como "superpoderes" para LLMs, permitindo que eles:**
- Acessem informações externas (APIs, bancos de dados)
- Executem ações (criar arquivos, enviar emails)
- Realizem cálculos complexos

**Por que usar Python?**
- Sintaxe simples e clara
- Vasto ecossistema de bibliotecas
- SDK Python MCP bem documentado
- Comunidade ativa

## 2. Configurando o Ambiente

### Instalação do Python e Ferramentas

```bash
# Verificar instalação do Python
python3 --version  # Deve mostrar Python 3.10.x ou superior

# Instalar uv (gerenciador de pacotes mais rápido que pip)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Criar e ativar ambiente virtual
mkdir mcp-server-tools && cd mcp-server-tools
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
uv add "mcp[cli]" httpx
```

## 3. Estrutura Básica do Servidor MCP

Um servidor MCP em Python requer três componentes principais:
- **Server**: classe central que gerencia comunicação e tools
- **Transport**: mecanismo para troca de mensagens (usaremos stdio)
- **Capabilities**: define funcionalidades oferecidas pelo servidor

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
import asyncio

# 1. Criar instância do servidor
mcp = FastMCP("meu-servidor-de-tools")

# 2. Declarar capabilities
@mcp.capabilities()
def server_capabilities():
    return {
        "tools": True,  # Este servidor oferece Tools
    }

# 3. Executar servidor com transporte stdio
async def main():
    async with stdio_server() as streams:
        await mcp.run(
            streams[0],  # Stream de leitura
            streams[1],  # Stream de escrita
            mcp.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. Implementando Tools

### Tool Simples com FastMCP (Decoradores)

```python
from mcp.server.fastmcp import FastMCP
import asyncio
import sys

mcp = FastMCP("meu-servidor-de-tools")

@mcp.capabilities()
def server_capabilities():
    return {"tools": True}

# Definir uma Tool simples usando decorador
@mcp.tool()
async def dizer_ola(nome: str) -> str:
    """Diz 'Olá' para a pessoa com o nome fornecido.

    Args:
        nome: O nome da pessoa a ser cumprimentada.
    """
    print(f"DEBUG: Tool dizer_ola chamada com nome={nome}", file=sys.stderr)
    return f"Olá, {nome}!"

# Exemplo de Tool com múltiplos parâmetros
@mcp.tool()
async def calcular(operacao: str, a: float, b: float) -> str:
    """Realiza operação matemática simples.
    
    Args:
        operacao: Tipo de operação ('soma', 'subtracao', 'multiplicacao', 'divisao')
        a: Primeiro número
        b: Segundo número
    """
    resultado = None
    if operacao == "soma":
        resultado = a + b
    elif operacao == "subtracao":
        resultado = a - b
    elif operacao == "multiplicacao":
        resultado = a * b
    elif operacao == "divisao":
        if b == 0:
            return "Erro: Divisão por zero!"
        resultado = a / b
    else:
        return f"Operação desconhecida: {operacao}"
    
    return f"Resultado de {a} {operacao} {b} = {resultado}"

async def main():
    async with stdio_server() as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

## 5. Executando e Testando o Servidor

1. **Execute o servidor**:
   ```bash
   python meu_servidor_tools.py
   ```

2. **Teste com o MCP Inspector**:
   ```bash
   # Em outro terminal
   npx @modelcontextprotocol/inspector
   ```

3. **No MCP Inspector**:
   - Selecione "Stdio Client" como Transport
   - Clique em "Connect"
   - Vá para a aba "Tools" 
   - Selecione a tool "dizer_ola"
   - Insira um nome no campo de argumento
   - Clique em "Call Tool"
   - Veja o resultado na seção "Output"

## 6. Depuração de Servidores MCP

### Técnicas Essenciais de Depuração

1. **Logging para stderr**:
   ```python
   import sys
   
   @mcp.tool()
   async def minha_tool(argumento: str) -> str:
       # Log para depuração (vai para stderr)
       print(f"DEBUG: minha_tool chamada com argumento: {argumento}", file=sys.stderr)
       try:
           # Lógica da Tool
           resultado = f"Processado: {argumento}"
           print(f"DEBUG: resultado: {resultado}", file=sys.stderr)
           return resultado
       except Exception as e:
           print(f"ERRO: {e}", file=sys.stderr)
           return f"Erro: {str(e)}"
   ```

2. **Verificar logs do Claude Desktop** (se estiver usando):
   ```bash
   tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
   ```

3. **MCP Inspector**:
   - Use a aba "Notifications"
   - Examine as mensagens de Request e Response

### Problemas Comuns e Soluções

1. **Tool não aparece no cliente**:
   - Verifique se declarou `"tools": True` nas capabilities
   - Reinicie o cliente (Inspector ou Claude)

2. **Chamada da Tool falha**:
   - Verifique logs (stderr)
   - Valide se os argumentos estão no formato correto
   - Confirme permissões (ex: acesso a arquivos)

## 7. Melhores Práticas

### Segurança

```python
import shlex
import asyncio

@mcp.tool()
async def executar_comando_seguro(comando: str) -> str:
    """Executa um comando de sistema (apenas comandos permitidos).

    Args:
        comando: O comando a ser executado
    """
    # Lista de comandos permitidos
    comandos_seguros = ["ls", "pwd", "whoami"]
    
    # Validação de input
    if comando not in comandos_seguros:
        return "Comando não permitido por razões de segurança."
    
    # Escape para prevenir shell injection
    comando_escapado = shlex.split(comando)
    
    # Execução do comando
    try:
        processo = await asyncio.create_subprocess_exec(
            *comando_escapado,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await processo.communicate()
        return f"Resultado:\n{stdout.decode()}"
    except Exception as e:
        return f"Erro: {str(e)}"
```

### Tratamento de Erros

```python
@mcp.tool()
async def ler_arquivo(caminho_arquivo: str) -> str:
    """Lê o conteúdo de um arquivo de texto.

    Args:
        caminho_arquivo: Caminho para o arquivo
    """
    try:
        with open(caminho_arquivo, "r") as f:
            conteudo = f.read()
            return conteudo
    except FileNotFoundError:
        return f"Erro: Arquivo não encontrado: '{caminho_arquivo}'"
    except PermissionError:
        return f"Erro: Permissão negada para ler '{caminho_arquivo}'"
    except Exception as e:
        return f"Erro inesperado: {str(e)}"
```

## 8. Tópicos Avançados

### Tools Assíncronas para Operações Longas

```python
import asyncio
import httpx

@mcp.tool()
async def buscar_dados_api(url: str) -> str:
    """Busca dados de uma API externa.

    Args:
        url: URL da API para consultar
    """
    print(f"DEBUG: Iniciando requisição para {url}", file=sys.stderr)
    
    # Requisição HTTP assíncrona
    async with httpx.AsyncClient() as cliente:
        try:
            response = await cliente.get(url, timeout=30.0)
            response.raise_for_status()  # Levanta exceção para códigos HTTP 4xx/5xx
            
            dados = response.json()
            return f"Dados recebidos: {dados}"
        except httpx.TimeoutException:
            return "Erro: A requisição excedeu o tempo limite"
        except httpx.HTTPStatusError as e:
            return f"Erro: A API retornou código {e.response.status_code}"
        except Exception as e:
            return f"Erro inesperado: {str(e)}"
```

### Esquemas de Input Complexos

```python
from typing import List, Dict, Literal, Optional

# Enum com Literal
OperacaoType = Literal["soma", "subtracao", "multiplicacao", "divisao"]

@mcp.tool()
async def calculadora_avancada(
    operacao: OperacaoType,  # Enum de operações permitidas
    a: float,
    b: float,
    arredondar: Optional[bool] = False  # Parâmetro opcional
) -> float:
    """Realiza operações matemáticas avançadas.

    Args:
        operacao: Tipo de operação (soma, subtracao, multiplicacao, divisao).
        a: Primeiro número.
        b: Segundo número.
        arredondar: Se True, arredonda o resultado (opcional, padrão False).
    """
    resultado = 0.0
    if operacao == "soma":
        resultado = a + b
    elif operacao == "subtracao":
        resultado = a - b
    elif operacao == "multiplicacao":
        resultado = a * b
    elif operacao == "divisao":
        if b == 0:
            raise ValueError("Divisão por zero!")
        resultado = a / b
    
    return round(resultado) if arredondar else resultado

# Tool com estruturas de dados complexas
@mcp.tool()
async def processar_pedido(
    cliente: Dict[str, str],  # Dicionário para dados do cliente
    itens: List[Dict[str, any]],  # Lista de dicionários para itens
    metodo_pagamento: Literal["credito", "debito", "pix"]
) -> str:
    """Processa um pedido de compra.

    Args:
        cliente: Dados do cliente (nome, email, telefone)
        itens: Lista de itens do pedido (id, nome, quantidade, preco)
        metodo_pagamento: Método de pagamento (credito, debito, pix)
    """
    # Validar cliente
    if "nome" not in cliente ou "email" not in cliente:
        return "Erro: Dados do cliente incompletos"
    
    # Calcular total
    total = sum(item.get("preco", 0) * item.get("quantidade", 0) for item in itens)
    
    # Processar pedido (simulação)
    return (
        f"Pedido processado com sucesso!\n"
        f"Cliente: {cliente['nome']} ({cliente['email']})\n"
        f"Total: R$ {total:.2f}\n"
        f"Pagamento: {metodo_pagamento}\n"
        f"Itens: {len(itens)}"
    )
```

## Conclusão

Com este guia, você está pronto para criar servidores MCP Python que oferecem Tools poderosas para LLMs. As possibilidades são infinitas: desde Tools simples que formatam textos até integrações complexas com APIs e bancos de dados.

Lembre-se de seguir as melhores práticas de segurança, tratamento de erros e documentação para criar Tools confiáveis e úteis.

**Próximos passos:**
- Explore a documentação oficial do MCP para recursos avançados
- Integre seu servidor com LLMs como Claude
- Crie Tools específicas para seus casos de uso