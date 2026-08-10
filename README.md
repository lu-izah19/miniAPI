# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação (sem mais conflito de path), modelos Pydantic separados da classe de estado, não depende mais de `input()`/menu de terminal para rodar, salva a senha como hash (`bcrypt`) em vez de texto puro, e está em processo de migração do armazenamento de um único usuário (variável global) para múltiplos usuários (dicionário indexado por email). Ainda restam ajustes de autorização e persistência real em banco de dados (ver "Próximos passos").

## Funcionalidades

- Cadastro de usuário (nome, email e senha)
- Login com verificação de credenciais
- Visualização de perfil do usuário logado
- Registro de eventos via `logging` (início da aplicação, boas-vindas, tentativas de login, opções inválidas)

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) *(versão API)*
- [Pydantic](https://docs.pydantic.dev/) *(validação de dados de entrada na versão API)*
- [bcrypt](https://pypi.org/project/bcrypt/) *(hash de senhas na versão API)*
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

- [ ] Finalizar a migração de `usuario_cadastro` para dicionário: `cadastro()` já grava por email (`usuario_cadastro[email] = novo_usuario`), mas `login()` e `perfil()` ainda usam a sintaxe antiga de objeto único (`usuario_cadastro.email`) e precisam ser ajustados para buscar o usuário certo dentro do dicionário
- [ ] Definir o formato de armazenamento definitivo dos dados de usuário (orientação da supervisora) — dicionário em memória é um passo intermediário; avaliar se o destino final é banco de dados
- [ ] Estruturar autorização de perfil de usuário

### Resolvido recentemente

- [x] Implementado hash de senha com `bcrypt` (`hashpw`/`gensalt` no cadastro, `checkpw` no login) — senha nunca mais é salva ou comparada em texto puro; testado com login válido e inválido
- [x] Iniciada a migração de `usuario_cadastro` de variável única para dicionário (`{}`), permitindo múltiplos usuários cadastrados ao mesmo tempo — `cadastro()` já ajustado
- [x] Corrigido `cadastro()`, `login()` e `perfil()` para salvarem/lerem os dados de uma instância real de `Usuario`, em vez de escrever/ler diretamente em atributos de classe
- [x] Removido o uso de `input()` e do loop de menu dentro das rotas
- [x] Removida a chamada de `inicio()` no final do arquivo (conflitava com o modelo de servidor do `uvicorn`)
- [x] Criados modelos Pydantic (`UsuarioCadastro`, `UsuarioInicio`, `UsuarioLogin`, `UsuarioPerfil`) separados da classe `Usuario`, que guarda o estado em memória
- [x] Corrigido o `__init__` de `Usuario` (faltava `self.` nos atributos)
- [x] Separadas as rotas de cadastro, login, início e perfil em paths próprios, eliminando o conflito de rotas duplicadas

## Aprendizados do projeto

Este projeto foi usado como base prática para consolidar conceitos de:

- Escopo de variáveis em Python (locais, de classe e de módulo/`global`) e compartilhamento de estado entre requisições diferentes
- Diferença entre um modelo Pydantic (`BaseModel`, usado para validar o corpo da requisição) e uma classe comum usada para guardar estado em memória
- Por que gravar em atributo de classe (`Classe.atributo = valor`) compartilha o dado entre todas as instâncias/requisições, e por que isso é um anti-padrão para estado por usuário
- Por que uma única variável global (mesmo guardando uma instância corretamente) só suporta um usuário por vez, e como um dicionário indexado por uma chave única (email) resolve isso
- Hash de senhas com `bcrypt`: por que é irreversível, por que usa salt, e por que a verificação (`checkpw`) nunca "descriptografa" a senha salva
- Boas práticas de segurança básica (nunca logar ou armazenar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`), path parameters e por que cada combinação verbo+path deve representar uma única ação

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
