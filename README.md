# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação (sem mais conflito de path), modelos Pydantic separados da classe de estado, e não depende mais de `input()`/menu de terminal para rodar. Ainda restam ajustes de segurança e persistência de dados (ver "Próximos passos").

## Funcionalidades

- Cadastro de usuário (nome, email e senha)
- Login com verificação de credenciais
- Visualização de perfil do usuário logado
- Registro de eventos via `logging` (início da aplicação, boas-vindas, tentativas de login, opções inválidas)

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) *(versão API)*
- [Pydantic](https://docs.pydantic.dev/) *(validação de dados de entrada na versão API)*
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
| `GET` | `/usuario` | Boas-vindas personalizada com o nome do usuário |
| `POST` | `/usuario` | Cadastro de novo usuário (nome, email e senha) |
| `POST` | `/login` | Login do usuário (email e senha) |
| `GET` | `/perfil` | Visualização de perfil do usuário logado |

> Cada ação passou a ter seu próprio path (`/usuario`, `/login`, `/perfil`), o que resolveu o conflito de rotas duplicadas que existia quando `cadastro`, `login` e `perfil` disputavam o mesmo endereço.

### Como rodar

```bash
uvicorn api:app --reload
```

Depois de rodar, a documentação interativa gerada automaticamente pelo FastAPI fica disponível em:

```
http://127.0.0.1:8000/docs
```

### Próximos passos

- [ ] Corrigir `cadastro()`, `login()` e `perfil()` para salvarem/lerem os dados em uma variável de estado separada (`usuario = Usuario(...)`), em vez de escrever/ler diretamente nos atributos da classe `Usuario`
- [ ] Implementar hash de senha com `bcrypt` (armazenamento seguro de credenciais)
- [ ] Definir o formato de armazenamento dos dados de usuário (orientação da supervisora)
- [ ] Estruturar autorização de perfil de usuário

### Resolvido recentemente

- [x] Removido o uso de `input()` e do loop de menu dentro das rotas
- [x] Removida a chamada de `inicio()` no final do arquivo (conflitava com o modelo de servidor do `uvicorn`)
- [x] Criados modelos Pydantic (`UsuarioCadastro`, `UsuarioInicio`, `UsuarioLogin`) separados da classe `Usuario`, que guarda o estado em memória
- [x] Corrigido o `__init__` de `Usuario` (faltava `self.` nos atributos)
- [x] Separadas as rotas de cadastro, login, início e perfil em paths próprios, eliminando o conflito de rotas duplicadas

## Aprendizados do projeto

Este projeto foi usado como base prática para consolidar conceitos de:

- Escopo de variáveis em Python (locais vs. globais) e compartilhamento de dados entre funções
- Diferença entre um modelo Pydantic (`BaseModel`, usado para validar o corpo da requisição) e uma classe comum usada para guardar estado em memória
- Boas práticas de segurança básica (nunca logar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`), path parameters e por que cada combinação verbo+path deve representar uma única ação

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
