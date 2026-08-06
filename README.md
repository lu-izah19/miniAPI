# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já possui rotas definidas, mas ainda está em processo de refatoração (migração de `input()` para dados recebidos via requisição).

## Funcionalidades

- Cadastro de usuário (nome, email e senha)
- Login com verificação de credenciais
- Visualização de perfil do usuário logado
- Registro de eventos via `logging` (início da aplicação, boas-vindas, tentativas de login, opções inválidas)

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) *(versão API)*
- Módulo `logging` da biblioteca padrão

## Versão terminal

Sistema com menu interativo no terminal, controlado por um loop `while True` com estrutura `if/elif/else`. Os dados do usuário são armazenados em memória durante a execução (sem persistência em banco de dados).

### Como rodar

```bash
python terminal.py
```

O programa vai pedir seu nome e, em seguida, exibir um menu com as opções:

```
1. Cadastro
2. Login
3. Perfil
4. Sair
```

## Versão API *(em andamento)*

Adaptação do mesmo sistema para o formato de rotas HTTP com FastAPI, como parte do aprendizado de desenvolvimento de APIs REST.

### Rotas definidas até o momento

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Rota inicial, mensagem de boas-vindas |
| `POST` | `/usuario/{email}/{senha}` | Cadastro de novo usuário |
| `GET` | `/usuario/{email}/{senha}` | Login do usuário |
| `GET` | `/usuario/{nome}/{email}` | Visualização de perfil |

### Como rodar

```bash
uvicorn api:app --reload
```

> **Nota:** no formato atual, ao rodar com `uvicorn`, a chamada de `inicio()` no final do arquivo entra em conflito com o modelo de servidor (fica esperando `input()` de terminal em vez de subir o servidor). Esse é justamente um dos itens listados em "Próximos passos" abaixo.

Depois de rodar, a documentação interativa gerada automaticamente pelo FastAPI fica disponível em:

```
http://127.0.0.1:8000/docs
```

### Próximos passos

- [ ] Remover o uso de `input()` dentro das funções de rota, substituindo por dados recebidos via parâmetros de URL ou corpo da requisição
- [ ] Ajustar a função `inicio()` para não rodar automaticamente junto com o servidor (conflito entre o modelo de terminal e o modelo de API)
- [ ] Corrigir a criação do `Usuario` em `cadastro()`: hoje ela sobrescreve o objeto sem o campo `nome`, perdendo o dado salvo anteriormente em `inicio()`
- [ ] Implementar hash de senha com `bcrypt` (armazenamento seguro de credenciais)
- [ ] Definir o formato de armazenamento dos dados de usuário (orientação da supervisora)
- [ ] Estruturar autorização de perfil de usuário

## Aprendizados do projeto

Este projeto foi usado como base prática para consolidar conceitos de:

- Escopo de variáveis em Python (locais vs. globais) e compartilhamento de dados entre funções
- Boas práticas de segurança básica (nunca logar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`) e path parameters

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
