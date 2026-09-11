# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), migrou o armazenamento para múltiplos usuários (dicionário indexado por email), e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). A rota `/perfil` já está protegida por token JWT (`Authorization: Bearer`), sem mais aceitar o email diretamente na URL, e trata token inválido/expirado com 401. O `/login` também trata email inexistente (404) e senha incorreta (401).

Foi adicionada autorização por papel (`user`/`admin`): o cadastro define `"user"` por padrão, e o papel **não é mais informado no login** — o `/login` busca o papel diretamente do cadastro e o inclui dentro do token JWT gerado, já que essa informação já existe desde o cadastro e não faz sentido pedir de novo. A rota `/admin` é restrita a usuários com papel `"admin"` (403 para quem não é) e tem conteúdo próprio: retorna a lista de **todos os usuários cadastrados** (nome e email de cada um), sem expor senha nem papel.

A API agora também cobre um CRUD mais completo de administração e de autogerenciamento de conta: um admin pode alterar o papel de qualquer usuário, excluir um usuário e resetar a senha de alguém que esqueceu; qualquer usuário logado pode editar o próprio perfil (nome, email e senha) ou deletar a própria conta. O tratamento de exceções de token também ficou mais específico: em vez de um `except:` genérico (que podia "engolir" até um `HTTPException` de 403 lançado dentro do mesmo `try`), agora cada rota protegida usa `except jwt.ExpiredSignatureError` e `except jwt.InvalidTokenError` separados, e a lógica de autorização (checar papel) ficou fora do bloco `try`, garantindo que 401 (token inválido) e 403 (sem permissão) nunca se confundam.

A edição do próprio perfil (`PATCH /perfil/usuario`) deixou de exigir todos os três campos de uma vez: agora usa um modelo Pydantic próprio (`UsuarioAlterarPerfil`), separado do modelo de cadastro, com `nome`, `email` e `senha` todos opcionais — a pessoa escolhe alterar só um, dois ou os três, e cada campo só é sobrescrito se for realmente enviado *(essa rota está em migração para SQL e, no momento, tem bugs conhecidos — ver seção de migração abaixo)*. O reset de senha por um admin (`PATCH /admin/usuario`) também ganhou uma validação: a nova senha é comparada (via `bcrypt.checkpw`) com o hash já salvo antes de qualquer coisa ser sobrescrita, e a rota recusa (409) se a senha nova for igual à anterior.

Os logs das rotas administrativas (`/admin/papel`, e as duas de `/admin/usuario` — exclusão e reset de senha) agora registram a trilha de auditoria completa: quem executou a ação (o admin, extraído do token), o que foi feito, em quem (o usuário-alvo) e o resultado — em vez de mensagens genéricas que não identificavam as partes envolvidas.

O email do usuário agora é criptografado em repouso: ele é salvo de forma reversível (`Fernet`, criptografia simétrica), diferente da senha (hash `bcrypt`, irreversível).

Foi adicionado um **usuário root fixo**, configurado inteiramente por variáveis de ambiente (`USUARIO_ROOT`, `SENHA_ROOT`, `EMAIL_ROOT`) e que **não é salvo junto com os demais usuários** — diferente de todos os outros. Essa decisão garante que o root sobreviva a qualquer operação de exclusão em massa dos usuários cadastrados, já que ele não depende do estado em memória (ou, agora, do banco) para existir. O `/login` reconhece o root comparando as credenciais recebidas diretamente com as variáveis de ambiente (antes de consultar o cadastro) e gera um token normalmente, com `"papel": "root"`.

Os tokens JWT gerados no `/login` (tanto para o root quanto para usuários comuns) agora **expiram automaticamente**: cada token carrega uma claim `exp`, definida como o momento atual (UTC) somado a 30 minutos. A validação da expiração já é feita nativamente pelo `jwt.decode()` em todas as rotas protegidas, que capturam essa condição pelo `except jwt.ExpiredSignatureError` já existente — nenhuma lógica extra precisou ser adicionada fora dos dois pontos onde o token é criado.

A opção de o usuário **excluir** a própria conta foi substituída por uma de **desativar** o próprio perfil (`PATCH /perfil/desativar`), que marca o usuário como inativo em vez de removê-lo do cadastro.

## 🚧 Migração para MariaDB (em andamento)

O projeto está migrando do armazenamento em dicionário (`usuario_cadastro`, em memória) para um banco de dados **MariaDB** real, usando `mysql.connector` para rodar as queries SQL diretamente (sem ORM). A tabela `usuarios` já foi criada e a conexão com o banco já está configurada via variáveis de ambiente.

Essa migração troca, rota por rota, tanto a *leitura* (dicionário → `SELECT` + `fetchone()`) quanto a *escrita* (mutação de objeto em memória → `UPDATE`/`INSERT`/`DELETE` + `commit()`) — e também exige reescrever a checagem de permissão (admin/root), já que o resultado do banco vem como um dicionário de colunas por linha (`usuario["coluna"]`), não como um objeto (`usuario.atributo`), e não é mais indexável por email como o dicionário antigo era.

**Rotas já migradas e funcionando:**
- `POST /login` — `SELECT` + `fetchone()` no lugar da busca no dicionário
- `GET /perfil` — token decodificado antes da consulta; leitura via `usuario["nome"]`
- `PATCH /perfil/desativar` — `UPDATE usuarios SET ativo = %s WHERE email = %s` + `commit()`
- `PATCH /admin/usuario` (reset de senha) — checagem de admin/root feita direto pelo `payload["papel"]` do token (sem consulta extra), comparação de senha com `bcrypt.checkpw` usando bytes dos dois lados, `UPDATE` + `commit()` reais

**Em migração, com bugs conhecidos:**
- `PATCH /perfil/usuario` (editar o próprio perfil) — os três campos opcionais (nome, senha, email) ainda não são totalmente independentes: alterar só o nome (sem senha) não salva nem confirma sucesso; alterar a senha sem trocar o email não executa o `commit()` (que hoje só roda dentro do bloco de troca de email). A checagem de "esse novo email já pertence a outro usuário" também ainda não foi implementada de fato no banco.

**Ainda não migradas** (continuam com a lógica antiga de dicionário, que não funciona mais contra o banco):
- `GET /admin` (listagem de usuários)
- `PATCH /admin/papel` (alterar papel de um usuário)
- `DELETE /admin/usuario` (excluir usuário)
- `POST /usuario` (cadastro) — ainda grava só em memória; precisa de um `INSERT` para os novos usuários aparecerem no banco e conseguirem logar depois

## Funcionalidades

- Cadastro de usuário (nome, email e senha), com papel `"user"` atribuído por padrão
- Login com verificação de credenciais e geração de token JWT contendo o papel do usuário (obtido do cadastro, não informado no login), com expiração de 30 minutos (`exp`)
- Usuário root fixo, definido por variáveis de ambiente e não persistido junto com os demais usuários, sobrevivendo a qualquer exclusão em massa de contas
- Visualização de perfil do usuário logado, protegida por token JWT
- Edição do próprio perfil (nome, email e/ou senha, todos opcionais — só é alterado o que for enviado), protegida por token JWT *(em migração — ver seção acima)*
- Desativação da própria conta (em vez de exclusão), protegida por token JWT
- Rota administrativa (`/admin`), acessível para usuários com papel `"admin"` ou para o root, que lista todos os usuários cadastrados (nome e email, sem senha)
- Alteração do papel de um usuário por um admin
- Exclusão de qualquer usuário por um admin
- Reset de senha de qualquer usuário por um admin (fluxo de "esqueci minha senha")
- Reset de senha recusa (409) se a senha nova for igual à anterior, verificado com `bcrypt.checkpw` antes de sobrescrever o hash salvo
- Tratamento de erros HTTP específicos: 404 (usuário não encontrado), 401 (senha, token inválido ou expirado), 403 (sem permissão de admin), 409 (email já em uso ou senha repetida)
- Registro de eventos via `logging`, incluindo trilha de auditoria completa nas ações administrativas (quem executou, o que foi feito, em quem, e o resultado)
- Criptografia reversível do email em repouso (`Fernet`), descriptografado apenas quando precisa ser exibido
- Testes automatizados com `pytest` e `TestClient`, cobrindo login, autenticação, autorização por papel, promoção de papel de fato, expiração de token e as ações de admin/perfil
- Padrão de estilo verificado por `flake8`, com configuração própria (`.flake8`)

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) *(versão API)*
- [Pydantic](https://docs.pydantic.dev/) *(validação de dados de entrada na versão API)*
- [bcrypt](https://pypi.org/project/bcrypt/) *(hash de senhas na versão API)*
- [PyJWT](https://pyjwt.readthedocs.io/) *(geração e validação de tokens JWT, incluindo expiração via claim `exp`)*
- [cryptography](https://cryptography.io/) *(criptografia simétrica reversível do email, via `Fernet`)*
- [python-dotenv](https://pypi.org/project/python-dotenv/) *(carregamento de `SECRET_KEY`, `FERNET_KEY`, das credenciais do usuário root e das credenciais do banco de dados a partir de `.env`)*
- [mysql-connector-python](https://pypi.org/project/mysql-connector-python/) *(conexão e execução de queries SQL contra o banco de dados MariaDB, em migração do dicionário em memória)*
- Módulo `datetime` da biblioteca padrão *(cálculo do horário de expiração dos tokens)*
- [pytest](https://docs.pytest.org/) *(testes automatizados)*
- [httpx](https://www.python-httpx.org/) *(requisitado internamente pelo `TestClient` do FastAPI/Starlette para simular requisições nos testes)*
- [flake8](https://flake8.pycqa.org/) *(linter de estilo e checagem estática, combinando `pycodestyle`, `pyflakes` e `mccabe`)*
- [autopep8](https://pypi.org/project/autopep8/) *(formatação automática, usado para corrigir a maior parte dos avisos do flake8)*
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
| `POST` | `/usuario` | Cadastro de novo usuário (nome, email e senha; papel `"user"` por padrão). ⚠️ Ainda grava só em memória, não no banco |
| `POST` | `/login` | Login do usuário (email e senha), ou do usuário root (credenciais vindas do `.env`). O papel é obtido do cadastro (ou fixado como `"root"`) e incluído no token JWT gerado, junto com uma expiração de 30 minutos (`exp`). 404 se o email não existir, 401 se a senha estiver errada. ✅ Migrado para SQL |
| `GET` | `/perfil` | Visualização de perfil do usuário logado, protegida por token JWT (`Authorization: Bearer`). 401 se o token for inválido/expirado. ✅ Migrado para SQL |
| `PATCH` | `/perfil/usuario` | Edição do próprio perfil (nome, email e/ou senha — todos opcionais, só altera o que for enviado), protegida por token JWT. ⚠️ Em migração, com bugs conhecidos na independência dos três campos e no `commit()` |
| `PATCH` | `/perfil/desativar` | Desativação da própria conta, protegida por token JWT. Não recebe nada no corpo — o usuário desativado é sempre o dono do token. ✅ Migrado para SQL |
| `GET` | `/admin` | Rota administrativa, protegida por token JWT e restrita a usuários com papel `"admin"` ou ao usuário root. Retorna a lista de todos os usuários cadastrados (nome e email descriptografado, sem senha). ⚠️ Ainda não migrada para SQL |
| `PATCH` | `/admin/papel` | Altera o papel (`user`/`admin`) de um usuário especificado por email. Restrita a admins ou ao root. ⚠️ Ainda não migrada para SQL |
| `DELETE` | `/admin/usuario` | Exclui um usuário especificado por email. Restrita a admins ou ao root. ⚠️ Ainda não migrada para SQL |
| `PATCH` | `/admin/usuario` | Reseta a senha de um usuário especificado por email (fluxo de "esqueci minha senha"). Restrita a admins ou ao root, checando o papel direto pelo token. 404 se o email não existir, 409 se a senha nova for igual à anterior. ✅ Migrado para SQL |

> Cada ação tem seu próprio path, o que resolveu o conflito de rotas duplicadas que existia quando `cadastro`, `login` e `perfil` disputavam o mesmo endereço.

### Configuração necessária

A rota `/login` depende de uma variável de ambiente `SECRET_KEY`, usada para assinar os tokens JWT. A criptografia do email depende de uma variável `FERNET_KEY`, usada para criptografar/descriptografar esse dado em repouso. O usuário root depende de três variáveis próprias (`USUARIO_ROOT`, `SENHA_ROOT`, `EMAIL_ROOT`), que definem suas credenciais fora do cadastro comum. A conexão com o MariaDB depende de `MARIADB_USER`, `MARIADB_PASSWORD` e `MARIADB_DATABASE`. Todas devem ser definidas em um arquivo `.env` na raiz do projeto (não incluído no repositório):

```
SECRET_KEY=<string aleatória gerada com secrets.token_hex(32)>
FERNET_KEY=<chave gerada com Fernet.generate_key()>
USUARIO_ROOT=<nome de exibição do usuário root>
SENHA_ROOT=<senha do usuário root>
EMAIL_ROOT=<email do usuário root>
MARIADB_USER=<usuário do banco MariaDB>
MARIADB_PASSWORD=<senha do banco MariaDB>
MARIADB_DATABASE=<nome do banco MariaDB>
```

### Como rodar

```bash
uvicorn api:app --reload
```

Depois de rodar, a documentação interativa gerada automaticamente pelo FastAPI fica disponível em:

```
http://127.0.0.1:8000/docs
```

## Testes automatizados

A pasta `tests/` contém a suíte de testes escrita com **pytest**, usando o `TestClient` do FastAPI (que depende de `httpx`) para simular requisições HTTP reais contra a aplicação, sem precisar do servidor rodando.

> ⚠️ Nota: a suíte de testes ainda foi escrita contra a versão em dicionário da API. Com a migração para MariaDB em andamento, alguns testes podem precisar de ajuste (mock ou banco de teste) assim que as rotas cobertas por eles forem migradas.

### Cobertura atual

- Login com senha correta: confirma status `200` e presença de `"token"` na resposta
- Login com senha incorreta: confirma status `401`
- Login com email não cadastrado: confirma status `404`
- Acesso a rota protegida sem token: confirma status `401`
- Acesso a rota protegida com token inválido: confirma status `401`
- Acesso a rota protegida com token expirado: gera um token com a claim `exp` já vencida (sem passar pelo fluxo normal de login) e confirma status `401`
- Login de um usuário comum (fluxo base para os testes de autorização): confirma status `200`
- Usuário comum tentando acessar `/admin`: confirma status `403`
- Usuário comum tentando `PATCH /admin/papel`: confirma status `403`
- Usuário comum tentando `DELETE /admin/usuario`: confirma status `403`
- Promoção de um usuário comum a admin por um admin (`PATCH /admin/papel`), confirmando que o papel muda de fato: o usuário promovido consegue logar de novo e acessar `/admin` com o novo token
- Edição do próprio perfil (`PATCH /perfil/usuario`): confirma status `200` e que a alteração não afeta o perfil de outra pessoa

Total: 12 testes.

### Como rodar

```bash
pip install pytest httpx
pytest -v
```

### Próximos passos dos testes

- Cobrir cadastro (sucesso e email duplicado)
- Formalizar a limpeza de estado como fixture (`@pytest.fixture`) em vez de chamada manual
- Cobrir a edição parcial de perfil (só nome, só email, só senha, e combinações entre os três)
- Cobrir a recusa (409) do reset de senha por admin quando a senha nova é igual à anterior
- Cobrir o login e o acesso à rota `/admin` pelo usuário root
- Adaptar/revisar os testes conforme cada rota for migrada para SQL

## Qualidade de código (lint)

O projeto usa **flake8** para checagem de estilo e alguns erros estáticos, combinando três ferramentas por baixo dos panos: `pycodestyle` (estilo/PEP 8), `pyflakes` (erros lógicos, como import não usado) e `mccabe` (complexidade). A configuração fica no arquivo `.flake8`, na raiz do projeto, com o limite de linha ajustado para 100 caracteres.

### Como rodar

```bash
pip install flake8
flake8 api.py
```

### Como corrigir automaticamente

Boa parte dos avisos de estilo (espaçamento, linhas em branco, indentação) pode ser corrigida sem edição manual, com o `autopep8`:

```bash
pip install autopep8
autopep8 --in-place --aggressive --max-line-length 100 api.py
```

O que sobra depois disso costuma ser erro de lógica (import/variável não usada, função redefinida) ou linha comprida por causa de uma condição booleana — esses o `autopep8` não corrige sozinho, de propósito, porque mudariam o comportamento do código ou a legibilidade dele.

> Nota: o código ainda tem indentação inconsistente em alguns trechos recém-migrados para SQL, resultado da edição manual durante a migração; vale rodar o `autopep8` de novo depois que as rotas restantes forem migradas.

## Aprendizados do projeto

Este projeto foi usado como base prática para consolidar conceitos de:

- Fundamentos de testes automatizados com `pytest`: convenção de nomes de arquivo (`test_*.py`, não `teste_*.py`) e de função (`def test_*()`) exigida para o pytest descobrir e coletar os testes
- Uso do `TestClient` (FastAPI/Starlette) para simular requisições HTTP reais contra a aplicação nos testes, em vez de chamar as funções de rota diretamente
- Isolamento entre testes: por que um teste não pode depender de estado deixado por outro, e como uma função auxiliar de limpeza (embrião do conceito de fixture) resolve isso
- Estrutura básica de um teste (`assert` para conferir o resultado de uma ação) e o padrão ação → conferência
- O que um `AssertionError` significa na prática: o `assert` da linha apontada rodou, mas o valor obtido não bateu com o esperado — e por que o traceback completo (não só o número da linha) é o que mostra os dois lados da comparação
- Diferença entre instalar um pacote dentro de uma virtualenv (`.venv`) e no Python do sistema operacional, e por que `sudo pip install` é um anti-padrão que pode mascarar o problema real (PATH apontando para o pip errado) em vez de resolvê-lo
- Criptografia simétrica reversível (`Fernet`) versus hash irreversível (`bcrypt`): quando usar cada uma, dependendo se o dado precisa ser lido de volta em algum momento
- Gerenciamento de segredos com variáveis de ambiente (`.env`), incluindo geração de chaves de criptografia e o cuidado de nunca commitar esse arquivo
- Conversão entre `str` e `bytes` (`.encode()`/`.decode()`) como pré-requisito para operações de criptografia e para comparação de hash com `bcrypt.checkpw`, inclusive quando um dos dois lados vem de uma consulta SQL (que devolve `str`, não `bytes`, dependendo do tipo da coluna)
- Diferença entre um modelo Pydantic (`BaseModel`, usado para validar o corpo da requisição) e uma classe comum usada para guardar estado em memória
- Hash de senhas com `bcrypt`: por que é irreversível, por que usa salt, e por que a verificação (`checkpw`) nunca "descriptografa" a senha salva
- Autenticação vs. autorização: "quem você é" vs. "o que você pode fazer/ver"
- Estrutura e propósito de um JWT (header, payload, signature) e por que ele permite autenticação stateless
- Por que o papel do usuário deve ser obtido de uma fonte confiável (o cadastro) e nunca informado livremente pelo próprio usuário no momento do login
- Trade-off entre incluir dados como o papel dentro do payload do token (mais rápido, mas "engessado" até o token expirar) versus consultar a fonte de dados a cada requisição (mais lento, porém sempre atualizado) — e como usar `payload["papel"]` direto do token evita uma consulta extra ao banco só para checar permissão
- Uso de `Depends` e `HTTPBearer` do FastAPI para extrair e validar o token do header `Authorization`, protegendo rotas sem depender de parâmetros na URL
- `try`/`except` como estratégia para lidar com falhas que só podem ser detectadas na hora de executar (como decodificar um token inválido), em vez de checadas antecipadamente com `if`
- Por que uma variável só existe depois da linha que a cria: consultar o banco usando um valor que só existe dentro do `payload` do token exige decodificar o token *antes* de rodar a consulta, nunca depois — reordenar essas duas etapas foi o bug mais recorrente da sessão de migração
- Diferença entre acessar uma coluna de uma linha do banco (`usuario["coluna"]`, um dicionário simples) e acessar o atributo de um objeto (`usuario.atributo`) — o resultado de `cursor.fetchone()` nunca tem atributos, só chaves
- Sintaxe de uma query `UPDATE` parametrizada (`SET coluna = %s WHERE condicao = %s`), a ordem dos placeholders `%s` correspondendo à ordem dos valores na tupla, e por que `UPDATE` sem um `cursor.execute` seguido de `conexao.commit()` não persiste nada — a mudança fica só na memória da requisição atual
- Diferença entre `SET` (o que muda) e `WHERE` (qual linha muda) dentro de um `UPDATE`, e por que usar uma coluna não-única (como nome) no `WHERE` é arriscado quando pode haver duplicatas
- Diferença entre `except` genérico e `except` específico por tipo de exceção (`jwt.ExpiredSignatureError`, `jwt.InvalidTokenError`), incluindo a ordem de precedência quando uma exceção é subclasse de outra, e o risco de um `except` genérico capturar até um `HTTPException` lançado dentro do próprio `try`
- Diferença entre `raise` (interrompe a execução e propaga um erro) e `return` (devolve um valor normalmente)
- Uso de `HTTPException` para devolver códigos de status HTTP apropriados a cada tipo de falha (404, 401, 403, 409), em vez de mensagens de erro genéricas com status 200
- Diferença entre os códigos 401 (não autenticado), 403 (autenticado, mas sem permissão) e 409 (conflito de dado, como email duplicado ou senha repetida)
- Controle de acesso baseado em papel (role-based access control): por que o papel de um usuário deve ser definido no cadastro (pela aplicação) e nunca escolhido livremente pelo próprio usuário
- Diferença entre uma ação sobre "si mesmo" (identificar o usuário pelo email do token) e uma ação de admin sobre "outra pessoa" (identificar o usuário-alvo por um email recebido no corpo da requisição) — e o risco de checar permissão sobre a pessoa errada quando as duas se confundem no código
- Por que blocos condicionais que deveriam ser independentes (como os três campos opcionais de uma edição parcial de perfil) precisam ficar no mesmo nível de indentação ("irmãos"), e não aninhados um dentro do outro — aninhar cria dependências artificiais entre campos que deveriam poder ser alterados de forma isolada
- Por que segredos (como `SECRET_KEY`, `FERNET_KEY`, as credenciais do usuário root e as credenciais do banco de dados) não devem ficar no código-fonte, e o papel de variáveis de ambiente (`.env`) nisso
- Boas práticas de segurança básica (nunca logar ou armazenar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Por que uma linha de log/`raise` colocada **depois** de um `return` ou de um `raise` no mesmo bloco nunca é executada (código morto), e por que a ordem das linhas dentro de uma função importa tanto quanto a lógica em si
- Como montar uma mensagem de log de auditoria completa (quem executou, o que fez, em quem, e o resultado), em vez de uma frase genérica que não identifica as partes envolvidas
- Separar um modelo Pydantic exclusivo para uma rota de edição parcial (`Optional[str] = None` em todos os campos), em vez de reaproveitar o modelo obrigatório do cadastro — e por que reaproveitar quebraria a validação da rota original
- Pegadinha de comparar uma senha nova com o hash salvo usando `bcrypt.checkpw()` **antes** de sobrescrever esse hash — comparar depois de já ter trocado o valor faz a checagem sempre dar `True`, porque a senha estaria sendo comparada com o hash dela mesma
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`, `PATCH`, `DELETE`), path parameters e por que cada combinação verbo+path deve representar uma única ação
- Uso de `ast.parse()` para isolar rapidamente um `SyntaxError` de um arquivo, sem precisar rodar o pytest inteiro por cima
- O que é um linter e como o `flake8` funciona por baixo dos panos, combinando `pycodestyle` (estilo), `pyflakes` (erros lógicos) e `mccabe` (complexidade) — e por que os códigos de erro têm essa cara (`E501`, `F401`, `C901`)

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
