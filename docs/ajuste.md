# Guia de Ajustes para Módulos GitHub

Este documento descreve o processo de análise e ajuste de módulos no projeto MCP GitHub Server, usando como exemplo o módulo de Actions.

## 1. Análise Inicial

### 1.1 Identificação dos Componentes
- Identificar todos os arquivos relacionados ao módulo
  - Schema/Models (ex: `actions_tools.py`)
  - Manager (ex: `actions.py`)
  - Handler (ex: `handlers.py`)
  - Tipos comuns (ex: `types.py`)
  - Utilitários (ex: `utils.py`)
  - Tratamento de erros (ex: `errors.py`)

### 1.2 Verificação de Dependências
- Verificar imports necessários
- Identificar dependências entre módulos
- Verificar se há circular imports

## 2. Organização do Schema (Input Models)

### 2.1 Estrutura Base
- Criar classes base para inputs comuns
- Exemplo:
  ```python
  class WorkflowInput(BaseInput):
      workflow_id: str
  
  class WorkflowRunInput(WorkflowInput):
      run_id: int
  ```

### 2.2 Validação
- Implementar validadores usando Pydantic
- Usar field_validator para validações complexas
- Centralizar validações no schema
- Exemplo:
  ```python
  @field_validator("workflow_id")
  @classmethod
  def validate_workflow_id(cls, v: str) -> str:
      if v.isdigit() or v.endswith('.yml'):
          return v
      raise ValueError("Invalid workflow ID")
  ```

### 2.3 Documentação
- Adicionar docstrings descritivas
- Incluir exemplos no schema
- Documentar todos os campos

## 3. Implementação do Manager

### 3.1 Responsabilidades
- Focar em operações com a API do GitHub
- Remover validações duplicadas (já feitas no schema)
- Tratar erros específicos da API

### 3.2 Tratamento de Erros
- Usar exceções específicas
- Mapear erros da API para exceções próprias
- Exemplo:
  ```python
  try:
      return self._repository.get_workflow(workflow_id)
  except Exception as e:
      if "Not Found" in str(e):
          raise NotFoundError(f"Workflow not found: {workflow_id}")
      raise GitHubError(f"Error getting workflow: {e}")
  ```

### 3.3 Tipagem
- Usar type hints apropriados
- Documentar tipos de retorno
- Usar tipos opcionais quando necessário

## 4. Configuração do Handler

### 4.1 Registro de Tools
- Registrar todas as tools necessárias
- Definir descrições claras
- Mapear schemas corretamente

### 4.2 Padronização de Chamadas
- Usar helper function para chamadas (ex: `call_tool`)
- Padronizar validação de argumentos
- Exemplo:
  ```python
  def call_tool(tool: Callable, schema: BaseModel, arguments: dict[str, Any]) -> Any:
      validated_arguments = schema.model_validate(arguments)
      return tool(**validated_arguments.model_dump(exclude_unset=True))
  ```

### 4.3 Organização do Código
- Agrupar tools por categoria
- Manter padrão de implementação
- Usar comentários para separação

## 5. Testes

### 5.1 Testes de Schema
- Testar validações
- Testar casos de erro
- Exemplo:
  ```python
  def test_workflow_id_validation():
      assert WorkflowInput(workflow_id="123").workflow_id == "123"
      with pytest.raises(ValueError):
          WorkflowInput(workflow_id="invalid")
  ```

### 5.2 Testes do Manager
- Testar chamadas à API
- Mockar respostas do GitHub
- Testar tratamento de erros

### 5.3 Testes do Handler
- Testar integração entre componentes
- Verificar fluxo completo
- Testar casos de erro

## 6. Documentação

### 6.1 Docstrings
- Documentar todas as classes e métodos
- Incluir exemplos de uso
- Documentar exceções

### 6.2 Exemplos de Uso
- Criar exemplos práticos
- Documentar casos comuns
- Exemplo:
  ```python
  # Listar workflows ativos
  workflows = await handler.call_tool("list_workflows", {"state": "active"})
  
  # Obter logs de uma execução
  logs = await handler.call_tool("get_workflow_run_logs", {"run_id": 12345})
  ```

## 7. Checklist Final

### 7.1 Verificação de Código
- [ ] Todas as validações estão no schema
- [ ] Manager está focado em operações da API
- [ ] Handler está padronizado
- [ ] Erros estão sendo tratados apropriadamente
- [ ] Documentação está completa
- [ ] Testes cobrem funcionalidades principais

### 7.2 Verificação de Uso
- [ ] Tools podem ser chamadas corretamente
- [ ] Erros retornam mensagens claras
- [ ] Validações funcionam como esperado
- [ ] Performance está adequada

### 7.3 Manutenibilidade
- [ ] Código está bem organizado
- [ ] Não há duplicação de lógica
- [ ] Fácil de adicionar novas features
- [ ] Fácil de entender e modificar 