# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), migrou o armazenamento para múltiplos usuários (dicionário indexado por email), e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). A rota `/perfil` já está protegida por token JWT (`Authorization: Bearer`), sem mais aceitar o email diretamente na URL, e trata token inválido/expirado com 401. O `/login` também trata email inexistente (404) e senha incorreta (401).

Foi adicionada autorização por papel (`user`/`admin`): o cadastro define `"user"` por padrão, e o papel **não é mais informado no login** — o `/login` busca o papel diretamente do cadastro e o inclui dentro do token JWT gerado, já que essa informação já existe desde o cadastro e não faz sentido pedir de novo. A rota `/admin` é restrita a usuários com papel `"admin"` (403 para quem não é) e agora tem conteúdo próprio: retorna a lista de **todos os usuários cadastrados** (nome e email de cada um), sem expor senha nem papel.

## Funcionalidades

- Cadastro de usuário (nome, email e senha), com papel `"user"` atribuído por padrão
- Login com verificação de credenciais e geração de token JWT contendo o papel do usuário (obtido do cadastro, não informado no login)
- Visualização de perfil do usuário logado, protegida por token JWT
- Rota administrativa (`/admin`), acessível apenas para usuários com papel `"admin"`, que lista todos os usuários cadastrados (nome e email, sem senha)
- Tratamento de erros HTTP específicos: 404 (email não encontrado), 401 (senha ou token inválido), 403 (sem permissão de admin)
- Registro de eventos via `logging` (início da aplicação, boas-vindas, acesso a rotas protegidas)

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
| `POST` | `/usuario` | Cadastro de novo usuário (nome, email e senha; papel `"user"` por padrão) |
| `POST` | `/login` | Login do usuário (email e senha). O papel é obtido do cadastro e incluído no token JWT gerado. 404 se o email não existir, 401 se a senha estiver errada |
| `GET` | `/perfil` | Visualização de perfil do usuário logado, protegida por token JWT (`Authorization: Bearer`). 401 se o token for inválido/expirado |
| `GET` | `/admin` | Rota administrativa, protegida por token JWT e restrita a usuários com papel `"admin"`. Retorna a lista de todos os usuários cadastrados (nome e email, sem senha). 401 se o token for inválido/expirado, 403 se o usuário não for admin |

> Cada ação passou a ter seu próprio path (`/usuario`, `/login`, `/perfil`, `/admin`), o que resolveu o conflito de rotas duplicadas que existia quando `cadastro`, `login` e `perfil` disputavam o mesmo endereço.

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

- [ ] Avaliar mecanismo para alterar o papel de um usuário já cadastrado (hoje só é definido manualmente no dicionário, não existe rota para isso)

### Resolvido recentemente

- [x] Removido o campo `papel` do modelo `UsuarioLogin`: o papel não é mais informado no login, e sim obtido diretamente do cadastro (`usuario_cadastro[email].papel`)
- [x] Token JWT gerado no `/login` agora inclui o papel do usuário no payload (`{"email": ..., "papel": ...}`), além do email
- [x] Rota `/admin` deixou de retornar apenas os dados do usuário logado (igual `/perfil`) e passou a listar todos os usuários cadastrados, percorrendo `usuario_cadastro` com um `for`, acumulando `nome` e `email` de cada um em uma lista (sem expor senha nem papel)
- [x] Protegida a rota `/perfil` para exigir token JWT (via header `Authorization: Bearer`, com `HTTPBearer` + `Depends`), em vez de aceitar o email diretamente na URL
- [x] Email extraído de dentro do token decodificado (`jwt.decode`), em vez de recebido como parâmetro de rota
- [x] Tratamento de token inválido/expirado com resposta 401, usando `try`/`except` em torno do `jwt.decode`
- [x] `/login` tratando email inexistente com 404 (`HTTPException`), em vez de deixar o `KeyError` estourar como erro 500
- [x] `/login` tratando senha incorreta com 401
- [x] Adicionado campo `papel` (`"user"` por padrão) na classe `Usuario`
- [x] Criada a rota `/admin`, restrita a usuários com papel `"admin"` (403 para quem não é admin), seguindo o mesmo padrão de autenticação via token da rota `/perfil`
- [x] Implementada geração de token JWT no `/login` (`jwt.encode`, assinado com `SECRET_KEY` carregada via `.env`/`python-dotenv`)
- [x] Implementado hash de senha com `bcrypt` (`hashpw`/`gensalt` no cadastro, `checkpw` no login) — senha nunca mais é salva ou comparada em texto puro
- [x] Migração de `usuario_cadastro` de variável única para dicionário (`{}`), permitindo múltiplos usuários cadastrados ao mesmo tempo
- [x] Corrigido `cadastro()`, `login()` e `perfil()` para salvarem/lerem os dados de uma instância real de `Usuario`, em vez de escrever/ler diretamente em atributos de classe
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
- Por que o papel do usuário deve ser obtido de uma fonte confiável (o cadastro) e nunca informado livremente pelo próprio usuário no momento do login
- Trade-off entre incluir dados como o papel dentro do payload do token (mais rápido, mas "engessado" até o token expirar) versus consultar a fonte de dados a cada requisição (mais lento, porém sempre atualizado)
- Uso de `Depends` e `HTTPBearer` do FastAPI para extrair e validar o token do header `Authorization`, protegendo rotas sem depender de parâmetros na URL
- `try`/`except` como estratégia para lidar com falhas que só podem ser detectadas na hora de executar (como decodificar um token inválido), em vez de checadas antecipadamente com `if`
- Diferença entre `raise` (interrompe a execução e propaga um erro) e `return` (devolve um valor normalmente)
- Uso de `HTTPException` para devolver códigos de status HTTP apropriados a cada tipo de falha (404, 401, 403), em vez de mensagens de erro genéricas com status 200
- Diferença entre os códigos 401 (não autenticado) e 403 (autenticado, mas sem permissão)
- Controle de acesso baseado em papel (role-based access control): por que o papel de um usuário deve ser definido no cadastro (pela aplicação) e nunca escolhido livremente pelo próprio usuário
- Como percorrer um dicionário com `for` para acumular resultados em uma lista com `.append()`, e por que declarar a lista **antes** do loop (não dentro dele) é essencial para não perder os dados de cada volta
- Por que um `return` dentro de um loop interrompe a execução na primeira volta, e por que ele deve ficar fora do `for` quando o objetivo é processar todos os itens
- Por que segredos (como a `SECRET_KEY`) não devem ficar no código-fonte, e o papel de variáveis de ambiente (`.env`) nisso
- Boas práticas de segurança básica (nunca logar ou armazenar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`), path parameters e por que cada combinação verbo+path deve representar uma única ação

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
