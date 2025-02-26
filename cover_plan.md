# Plano de Melhoria de Cobertura de Testes

## Status Atual
- Cobertura Geral: 52% (504/968 linhas cobertas)
- 0 testes falhando
- 65 testes passando

## 1. Corrigir Testes Quebrados

### Files Module
- [x] Corrigir assinaturas dos métodos em test_files.py
  - [x] Atualizar test_get_file_contents
  - [x] Atualizar test_create_file
  - [x] Atualizar test_update_file
  - [x] Atualizar test_delete_file
  - [x] Atualizar test_get_directory_contents
  - [x] Atualizar test_create_directory
  - [x] Atualizar test_push_files
  - [x] Atualizar test_push_directory

### Files Extra Module
- [x] Corrigir configurações em test_files_extra.py
  - [x] Remover parâmetro 'owner' de GetFileContentsConfig
  - [x] Remover parâmetro 'owner' de CreateOrUpdateFileConfig
  - [x] Remover parâmetro 'owner' de PushFilesContentConfig
  - [x] Remover parâmetro 'owner' de PushFilesFromPathConfig

### Repository Module
- [x] Corrigir mocks em test_repository.py
  - [x] Ajustar test_fork_repository
  - [x] Ajustar test_fork_repository_with_org
  - [x] Ajustar test_context_manager

## 2. Adicionar Novos Testes

### Common Module (utils.py - 51% cobertura)
- [x] Funções de codificação/decodificação
  - [x] test_encode_content
  - [x] test_decode_content
- [x] Validações
  - [x] test_validate_branch_name
  - [x] test_validate_file_path
  - [x] test_validate_commit_message
- [x] Manipulação de datas
  - [x] test_format_datetime
  - [x] test_parse_datetime

### Operations Module

#### Commits (97% cobertura)
- [x] Operações básicas
  - [x] test_get_commit
  - [x] test_list_commits
  - [x] test_compare_commits
- [x] Casos especiais
  - [x] test_list_commits_no_filters
  - [x] test_list_commits_with_filters

#### Search (100% cobertura)
- [x] Busca de issues
  - [x] test_search_issues_basic
  - [x] test_search_issues_with_filters
- [x] Busca de pull requests
  - [x] test_search_pulls_basic
  - [x] test_search_pulls_with_filters
- [x] Busca de código
  - [x] test_search_code_basic
- [x] Busca de commits
  - [x] test_search_commits_basic
  - [x] test_search_commits_with_date_range

### Server Module (0% cobertura)

#### App (app.py)
- [ ] Configuração do servidor
  - [ ] test_app_initialization
  - [ ] test_app_middleware
  - [ ] test_app_cors
- [ ] Rotas básicas
  - [ ] test_health_check
  - [ ] test_version_endpoint

#### Handlers (handlers.py)
- [ ] Endpoints de repositório
  - [ ] test_create_repository_handler
  - [ ] test_get_repository_handler
  - [ ] test_delete_repository_handler
- [ ] Endpoints de branches
  - [ ] test_create_branch_handler
  - [ ] test_protect_branch_handler
  - [ ] test_delete_branch_handler
- [ ] Endpoints de issues
  - [ ] test_create_issue_handler
  - [ ] test_update_issue_handler
  - [ ] test_list_issues_handler
- [ ] Endpoints de pull requests
  - [ ] test_create_pr_handler
  - [ ] test_merge_pr_handler
  - [ ] test_close_pr_handler

## 3. Melhorar Cobertura de Casos de Erro

### Validação de Entrada
- [ ] Testar parâmetros inválidos
  - [ ] test_invalid_branch_names
  - [ ] test_invalid_file_paths
  - [ ] test_invalid_commit_messages
  - [ ] test_invalid_configurations

### Tratamento de Exceções
- [ ] Testar erros da API do GitHub
  - [ ] test_rate_limit_exceeded
  - [ ] test_authentication_failed
  - [ ] test_permission_denied
  - [ ] test_resource_not_found
- [ ] Testar erros de rede
  - [ ] test_connection_timeout
  - [ ] test_connection_error
  - [ ] test_bad_gateway

## 4. Priorização

### Fase 1 - Alta Prioridade
- [x] Corrigir testes quebrados em files.py
- [x] Corrigir testes quebrados em repository.py

### Fase 2 - Média Prioridade
- [x] Implementar testes para utils.py
  - [x] Testes de codificação/decodificação
  - [x] Testes de validação
  - [x] Testes de manipulação de datas
- [x] Implementar testes para commits.py
- [x] Implementar testes para search.py

### Fase 3 - Baixa Prioridade
- [ ] Implementar testes para o módulo server
- [ ] Melhorar cobertura de casos de erro
- [ ] Adicionar testes de integração

## Métricas de Sucesso
- [ ] Atingir cobertura geral > 85%
- [ ] Zero testes falhando
- [ ] Todos os módulos com cobertura > 75%
- [ ] Documentação de testes atualizada 