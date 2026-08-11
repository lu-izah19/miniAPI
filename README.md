# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), migrou o armazenamento para múltiplos usuários (dicionário indexado por email), e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). Falta usar esse token para proteger a rota `/perfil` — hoje ela ainda aceita o email direto na URL, sem checar autenticação. Persistência real em banco de dados também segue pendente (ver "Próximos passos").

## Funcionalidades

- Cadastro de usuário (nome, email e senha)
- Login com verificação de credenciais e geração de token JWT
- Visualização de perfil do usuário logado
- Registro de eventos via `logging` (início da aplicação, boas-vindas, tentativas de login, opções inválidas)

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) *(versão API)*
- [Pydantic](https://docs.pydantic.dev/) *(validação de dados de entrada na versão API)*
- [bcrypt](https://pypi.org/project/bcrypt/) *(hash de senhas na versão API)*
- [PyJWT](https://pyjwt.readthedocs.io/) *(geração e validação de tokens JWT)*
- [python-dotenv](https://pypi.org/project/python-dotenv/) *(carregamento da `SECRET_KEY` a partir de `.env`)*
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
| `POST` | `/login` | Login do usuário (email e senha), retorna token JWT |
| `GET` | `/perfil/{email}` | Visualização de perfil do usuário *(ainda sem checagem de autenticação)* |

> Cada ação passou a ter seu próprio path (`/usuario`, `/login`, `/perfil`), o que resolveu o conflito de rotas duplicadas que existia quando `cadastro`, `login` e `perfil` disputavam o mesmo endereço.

### Configuração necessária

A rota `/login` depende de uma variável de ambiente `SECRET_KEY`, usada para assinar os tokens JWT. Ela deve ser definida em um arquivo `.env` na raiz do projeto (não incluído no repositório):

```
SECRET_KEY=<string aleatória gerada com secrets.token_hex(32)>
```

### Como rodar

```bash
uvicorn api:app --reload
```

Depois de rodar, a documentação interativa gerada automaticamente pelo FastAPI fica disponível em:

```
http://127.0.0.1:8000/docs
```

### Próximos passos

- [ ] Proteger a rota `/perfil` para exigir o token JWT (via header `Authorization: Bearer`), em vez de aceitar o email diretamente na URL
- [ ] Extrair o email de dentro do token decodificado, em vez de receber como parâmetro de rota
- [ ] Tratar tokens inválidos/expirados com resposta 401
- [ ] Definir o formato de armazenamento definitivo dos dados de usuário (orientação da supervisora: dicionário em memória, sem previsão de migração para banco de dados por ora)

### Resolvido recentemente

- [x] Implementada geração de token JWT no `/login` (`jwt.encode`, assinado com `SECRET_KEY` carregada via `.env`/`python-dotenv`)
- [x] Removido `import email` desnecessário, que colidia silenciosamente com a variável local `email` usada nas rotas
- [x] Implementado hash de senha com `bcrypt` (`hashpw`/`gensalt` no cadastro, `checkpw` no login) — senha nunca mais é salva ou comparada em texto puro
- [x] Migração de `usuario_cadastro` de variável única para dicionário (`{}`), permitindo múltiplos usuários cadastrados ao mesmo tempo
- [x] Corrigido `cadastro()`, `login()` e `perfil()` para salvarem/lerem os dados de uma instância real de `Usuario`, em vez de escrever/ler diretamente em atributos de classe
- [x] Migrado `/perfil` de rota GET-com-corpo para GET-com-path-param (`/perfil/{email}`), alinhado com convenção REST
- [x] Removido o uso de `input()` e do loop de menu dentro das rotas
- [x] Criados modelos Pydantic (`UsuarioCadastro`, `UsuarioInicio`, `UsuarioLogin`, `UsuarioPerfil`) separados da classe `Usuario`, que guarda o estado em memória
- [x] Separadas as rotas de cadastro, login, início e perfil em paths próprios, eliminando o conflito de rotas duplicadas

## Aprendizados do projeto

Este projeto foi usado como base prática para consolidar conceitos de:

- Escopo de variáveis em Python (locais, de classe e de módulo/`global`) e compartilhamento de estado entre requisições diferentes
- Diferença entre um modelo Pydantic (`BaseModel`, usado para validar o corpo da requisição) e uma classe comum usada para guardar estado em memória
- Por que gravar em atributo de classe (`Classe.atributo = valor`) compartilha o dado entre todas as instâncias/requisições, e por que isso é um anti-padrão para estado por usuário
- Por que uma única variável global (mesmo guardando uma instância corretamente) só suporta um usuário por vez, e como um dicionário indexado por uma chave única (email) resolve isso
- Hash de senhas com `bcrypt`: por que é irreversível, por que usa salt, e por que a verificação (`checkpw`) nunca "descriptografa" a senha salva
- Autenticação vs. autorização: "quem você é" vs. "o que você pode fazer/ver"
- Estrutura e propósito de um JWT (header, payload, signature) e por que ele permite autenticação stateless
- Por que segredos (como a `SECRET_KEY`) não devem ficar no código-fonte, e o papel de variáveis de ambiente (`.env`) nisso
- Boas práticas de segurança básica (nunca logar ou armazenar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`), path parameters e por que cada combinação verbo+path deve representar uma única ação

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
