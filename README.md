# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), migrou o armazenamento para múltiplos usuários (dicionário indexado por email), e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). A rota `/perfil` já está protegida por token JWT (`Authorization: Bearer`), sem mais aceitar o email diretamente na URL, e trata token inválido/expirado com 401. O `/login` também trata email inexistente (404) e senha incorreta (401).

Foi adicionada autorização por papel (`user`/`admin`): o cadastro define `"user"` por padrão, e o papel **não é mais informado no login** — o `/login` busca o papel diretamente do cadastro e o inclui dentro do token JWT gerado, já que essa informação já existe desde o cadastro e não faz sentido pedir de novo. A rota `/admin` é restrita a usuários com papel `"admin"` (403 para quem não é) e tem conteúdo próprio: retorna a lista de **todos os usuários cadastrados** (nome e email de cada um), sem expor senha nem papel.

A API agora também cobre um CRUD mais completo de administração e de autogerenciamento de conta: um admin pode alterar o papel de qualquer usuário, excluir um usuário e resetar a senha de alguém que esqueceu; qualquer usuário logado pode editar o próprio perfil (nome, email e senha) ou deletar a própria conta. O tratamento de exceções de token também ficou mais específico: em vez de um `except:` genérico (que podia "engolir" até um `HTTPException` de 403 lançado dentro do mesmo `try`), agora cada rota protegida usa `except jwt.ExpiredSignatureError` e `except jwt.InvalidTokenError` separados, e a lógica de autorização (checar papel) ficou fora do bloco `try`, garantindo que 401 (token inválido) e 403 (sem permissão) nunca se confundam.

A edição do próprio perfil (`PATCH /perfil/usuario`) deixou de exigir todos os três campos de uma vez: agora usa um modelo Pydantic próprio (`UsuarioAlterarPerfil`), separado do modelo de cadastro, com `nome`, `email` e `senha` todos opcionais — a pessoa escolhe alterar só um, dois ou os três, e cada campo só é sobrescrito se for realmente enviado. O reset de senha por um admin (`PATCH /admin/usuario`) também ganhou uma validação: a nova senha é comparada (via `bcrypt.checkpw`) com o hash já salvo antes de qualquer coisa ser sobrescrita, e a rota recusa (409) se a senha nova for igual à anterior.

Os logs das rotas administrativas (`/admin/papel`, e as duas de `/admin/usuario` — exclusão e reset de senha) agora registram a trilha de auditoria completa: quem executou a ação (o admin, extraído do token), o que foi feito, em quem (o usuário-alvo) e o resultado — em vez de mensagens genéricas que não identificavam as partes envolvidas.

O email do usuário agora é criptografado em repouso: ele é salvo de forma reversível (`Fernet`, criptografia simétrica) dentro do objeto `Usuario`, diferente da senha (hash `bcrypt`, irreversível). O dicionário `usuario_cadastro` continua indexado pelo email em texto puro (necessário, já que a criptografia gera um resultado diferente a cada execução), enquanto o campo `.email` guardado dentro de cada objeto `Usuario` fica sempre criptografado, sendo descriptografado apenas nas rotas que precisam devolvê-lo (como `/admin`).

Foi adicionado um **usuário root fixo**, configurado inteiramente por variáveis de ambiente (`USUARIO_ROOT`, `SENHA_ROOT`, `EMAIL_ROOT`) e que **não é salvo no dicionário `usuario_cadastro`** — diferente de todos os outros usuários. Essa decisão garante que o root sobreviva a qualquer operação de exclusão em massa dos usuários cadastrados, já que ele não depende do estado em memória para existir. O `/login` reconhece o root comparando as credenciais recebidas diretamente com as variáveis de ambiente (antes de consultar o dicionário) e gera um token normalmente, com `"papel": "root"`. A rota `/admin` também trata o root como um caso especial (checando `payload["papel"] == "root"`), sem tentar buscá-lo no dicionário, evitando um `KeyError` que ocorreria se ele fosse tratado como um usuário comum.

Essa mesma verificação — checar primeiro se quem chama é o root, antes de qualquer busca no dicionário — precisou ser replicada nas outras rotas administrativas: `PATCH /admin/papel`, `DELETE /admin/usuario` e `PATCH /admin/usuario` (reset de senha). Elas originalmente checavam direto se o papel armazenado no cadastro era `"admin"`, sem considerar o root como um caso à parte, o que causava um `KeyError: 'admin@gmail.com.br'` sempre que o próprio root chamava uma dessas rotas (o email dele nunca existiu em `usuario_cadastro`). A correção replicou em todas elas o mesmo padrão já usado em `/admin`: checar `payload["papel"] == "root"` antes de qualquer acesso ao dicionário.

Os tokens JWT gerados no `/login` (tanto para o root quanto para usuários comuns) agora **expiram automaticamente**: cada token carrega uma claim `exp`, definida como o momento atual (UTC) somado a 30 minutos. A validação da expiração já é feita nativamente pelo `jwt.decode()` em todas as rotas protegidas, que capturam essa condição pelo `except jwt.ExpiredSignatureError` já existente — nenhuma lógica extra precisou ser adicionada fora dos dois pontos onde o token é criado.

A opção de o usuário **excluir** a própria conta foi substituída por uma de **desativar** o próprio perfil (`PATCH /perfil/desativar`), que marca o usuário como inativo em vez de removê-lo do dicionário `usuario_cadastro`.

A suíte de **testes automatizados** com `pytest` foi expandida e agora cobre o fluxo completo: login (sucesso, senha errada, email inexistente), acesso a rota protegida com e sem token válido, autorização por papel (usuário comum barrado de ações de admin), promoção de papel de fato (um admin promove um usuário e o usuário promovido volta a logar e acessa `/admin` com o novo token), expiração de token JWT, e as ações de admin e de autogerenciamento de perfil — tudo passando (12 testes, isolamento de estado entre eles).

O código também passou a seguir um padrão de estilo verificado por **linter** (`flake8`): o `api.py` foi reorganizado (imports agrupados no topo, 2 linhas em branco entre definições, sem espaço em parâmetro nomeado, sem linha comprida, operadores lógicos sempre no início da linha de continuação, sem espaço em branco sobrando no fim de linha) e roda hoje com **zero avisos** de lint.

## Funcionalidades

- Cadastro de usuário (nome, email e senha), com papel `"user"` atribuído por padrão
- Login com verificação de credenciais e geração de token JWT contendo o papel do usuário (obtido do cadastro, não informado no login), com expiração de 30 minutos (`exp`)
- Usuário root fixo, definido por variáveis de ambiente e não persistido no dicionário de usuários, sobrevivendo a qualquer exclusão em massa de contas — tratado como caso especial (checado antes de qualquer acesso ao dicionário) em todas as rotas administrativas
- Visualização de perfil do usuário logado, protegida por token JWT
- Edição do próprio perfil (nome, email e/ou senha, todos opcionais — só é alterado o que for enviado), protegida por token JWT, com verificação de conflito de email
- Desativação da própria conta (em vez de exclusão), protegida por token JWT
- Rota administrativa (`/admin`), acessível para usuários com papel `"admin"` ou para o root, que lista todos os usuários cadastrados (nome e email, sem senha)
- Alteração do papel de um usuário por um admin, sem precisar editar o dicionário manualmente
- Exclusão de qualquer usuário por um admin
- Reset de senha de qualquer usuário por um admin (fluxo de "esqueci minha senha")
- Reset de senha recusa (409) se a senha nova for igual à anterior, verificado com `bcrypt.checkpw` antes de sobrescrever o hash salvo
- Tratamento de erros HTTP específicos: 404 (usuário não encontrado), 401 (senha, token inválido ou expirado), 403 (sem permissão de admin), 409 (email já em uso ou senha repetida)
- Registro de eventos via `logging`, incluindo trilha de auditoria completa nas ações administrativas (quem executou, o que foi feito, em quem, e o resultado)
- Criptografia reversível do email em repouso (`Fernet`), descriptografado apenas quando precisa ser exibido
- Testes automatizados com `pytest` e `TestClient`, cobrindo login, autenticação, autorização por papel, promoção de papel de fato, expiração de token e as ações de admin/perfil
- Padrão de estilo verificado por `flake8`, com configuração própria (`.flake8`) e código passando sem nenhum aviso

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/) *(versão API)*
- [Pydantic](https://docs.pydantic.dev/) *(validação de dados de entrada na versão API)*
- [bcrypt](https://pypi.org/project/bcrypt/) *(hash de senhas na versão API)*
- [PyJWT](https://pyjwt.readthedocs.io/) *(geração e validação de tokens JWT, incluindo expiração via claim `exp`)*
- [cryptography](https://cryptography.io/) *(criptografia simétrica reversível do email, via `Fernet`)*
- [python-dotenv](https://pypi.org/project/python-dotenv/) *(carregamento de `SECRET_KEY`, `FERNET_KEY` e das credenciais do usuário root a partir de `.env`)*
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
| `POST` | `/usuario` | Cadastro de novo usuário (nome, email e senha; papel `"user"` por padrão). O email é criptografado antes de ser salvo no objeto `Usuario` |
| `POST` | `/login` | Login do usuário (email e senha), ou do usuário root (credenciais vindas do `.env`). O papel é obtido do cadastro (ou fixado como `"root"`) e incluído no token JWT gerado, junto com uma expiração de 30 minutos (`exp`). 404 se o email não existir, 401 se a senha estiver errada |
| `GET` | `/perfil` | Visualização de perfil do usuário logado, protegida por token JWT (`Authorization: Bearer`). 401 se o token for inválido/expirado |
| `PATCH` | `/perfil/usuario` | Edição do próprio perfil (nome, email e/ou senha — todos opcionais, só altera o que for enviado), protegida por token JWT. O usuário editado é sempre o dono do token (nunca um email vindo do corpo). 409 se o novo email já pertencer a outro usuário. Se o email for alterado, o novo é criptografado antes de ser salvo |
| `PATCH` | `/perfil/desativar` | Desativação da própria conta, protegida por token JWT. Não recebe nada no corpo — o usuário desativado é sempre o dono do token; o registro continua no dicionário, apenas marcado como inativo |
| `GET` | `/admin` | Rota administrativa, protegida por token JWT e restrita a usuários com papel `"admin"` ou ao usuário root. Retorna a lista de todos os usuários cadastrados (nome e email descriptografado, sem senha). 401 se o token for inválido/expirado, 403 se o usuário não for admin/root |
| `PATCH` | `/admin/papel` | Altera o papel (`user`/`admin`) de um usuário especificado por email. Restrita a admins ou ao root (o root é checado antes de qualquer busca no dicionário, evitando `KeyError`). 404 se o email não existir, 403 se quem chama não for admin |
| `DELETE` | `/admin/usuario` | Exclui um usuário especificado por email. Restrita a admins ou ao root (mesma checagem de root primeiro). 404 se o email não existir, 403 se quem chama não for admin |
| `PATCH` | `/admin/usuario` | Reseta a senha de um usuário especificado por email (fluxo de "esqueci minha senha"). Restrita a admins ou ao root (mesma checagem de root primeiro). 404 se o email não existir, 403 se quem chama não for admin, 409 se a senha nova for igual à anterior |

> Cada ação tem seu próprio path, o que resolveu o conflito de rotas duplicadas que existia quando `cadastro`, `login` e `perfil` disputavam o mesmo endereço.

### Configuração necessária

A rota `/login` depende de uma variável de ambiente `SECRET_KEY`, usada para assinar os tokens JWT. A criptografia do email depende de uma variável `FERNET_KEY`, usada para criptografar/descriptografar esse dado em repouso. O usuário root depende de três variáveis próprias (`USUARIO_ROOT`, `SENHA_ROOT`, `EMAIL_ROOT`), que definem suas credenciais fora do dicionário de usuários. Todas devem ser definidas em um arquivo `.env` na raiz do projeto (não incluído no repositório):

```
SECRET_KEY=<string aleatória gerada com secrets.token_hex(32)>
FERNET_KEY=<chave gerada com Fernet.generate_key()>
USUARIO_ROOT=<nome de exibição do usuário root>
SENHA_ROOT=<senha do usuário root>
EMAIL_ROOT=<email do usuário root>
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

Cada teste começa limpando o dicionário `usuario_cadastro` (função auxiliar `limpar_cadastro()`), garantindo que um teste não interfira no resultado do outro — isolamento de estado entre testes.

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

Total: 12 testes, todos passando.

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

### Status atual

`api.py` roda com **zero avisos** de flake8.

## Aprendizados do projeto

Este projeto foi usado como base prática para consolidar conceitos de:

- Fundamentos de testes automatizados com `pytest`: convenção de nomes de arquivo (`test_*.py`, não `teste_*.py`) e de função (`def test_*()`) exigida para o pytest descobrir e coletar os testes
- Uso do `TestClient` (FastAPI/Starlette) para simular requisições HTTP reais contra a aplicação nos testes, em vez de chamar as funções de rota diretamente
- Isolamento entre testes: por que um teste não pode depender de estado deixado por outro, e como uma função auxiliar de limpeza (embrião do conceito de fixture) resolve isso
- Estrutura básica de um teste (`assert` para conferir o resultado de uma ação) e o padrão ação → conferência
- O que um `AssertionError` significa na prática: o `assert` da linha apontada rodou, mas o valor obtido não bateu com o esperado — e por que o traceback completo (não só o número da linha) é o que mostra os dois lados da comparação
- Diferença entre instalar um pacote dentro de uma virtualenv (`.venv`) e no Python do sistema operacional, e por que `sudo pip install` é um anti-padrão que pode mascarar o problema real (PATH apontando para o pip errado) em vez de resolvê-lo
- Criptografia simétrica reversível (`Fernet`) versus hash irreversível (`bcrypt`): quando usar cada uma, dependendo se o dado precisa ser lido de volta em algum momento
- Por que um valor criptografado com `Fernet` muda a cada execução (mesmo para o mesmo texto de entrada), e por que isso impede usá-lo como chave de busca em um dicionário — a chave precisa continuar em texto puro, e só o valor guardado dentro do objeto é que fica criptografado
- Gerenciamento de segredos com variáveis de ambiente (`.env`), incluindo geração de chaves de criptografia e o cuidado de nunca commitar esse arquivo
- Conversão entre `str` e `bytes` (`.encode()`/`.decode()`) como pré-requisito para operações de criptografia, que trabalham a nível de bytes
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
- Diferença entre `except` genérico e `except` específico por tipo de exceção (`jwt.ExpiredSignatureError`, `jwt.InvalidTokenError`), incluindo a ordem de precedência quando uma exceção é subclasse de outra, e o risco de um `except` genérico capturar até um `HTTPException` lançado dentro do próprio `try`
- Diferença entre `raise` (interrompe a execução e propaga um erro) e `return` (devolve um valor normalmente)
- Uso de `HTTPException` para devolver códigos de status HTTP apropriados a cada tipo de falha (404, 401, 403, 409), em vez de mensagens de erro genéricas com status 200
- Diferença entre os códigos 401 (não autenticado), 403 (autenticado, mas sem permissão) e 409 (conflito de dado, como email duplicado ou senha repetida)
- Controle de acesso baseado em papel (role-based access control): por que o papel de um usuário deve ser definido no cadastro (pela aplicação) e nunca escolhido livremente pelo próprio usuário
- Diferença entre uma ação sobre "si mesmo" (identificar o usuário pelo email do token) e uma ação de admin sobre "outra pessoa" (identificar o usuário-alvo por um email recebido no corpo da requisição)
- `KeyError` ao acessar uma chave inexistente em um dicionário, e por que checar a existência da chave antes (`if chave in dicionario`) sempre precisa vir antes de qualquer outro acesso a essa mesma chave, mesmo dentro de uma condição diferente (como uma comparação de senha)
- Como a **ordem** das checagens de autorização importa tanto quanto a lógica em si: checar `usuario_cadastro[payload["email"]].papel == "admin"` **antes** de checar se quem chama é o root (que nunca está no dicionário) gera um `KeyError`, mesmo que a regra de "quem pode fazer o quê" esteja certa — a causa era a ordem das condições, não a regra
- `del` para remover uma entrada de um dicionário
- Por que, num dicionário indexado por email, alterar apenas o atributo `.email` de um objeto não move o registro — é preciso criar a entrada na nova chave e apagar a antiga — e por que é necessário checar conflito de email antes de permitir a troca
- Como percorrer um dicionário com `for` para acumular resultados em uma lista com `.append()`, e por que declarar a lista **antes** do loop (não dentro dele) é essencial para não perder os dados de cada volta
- Por que um `return` dentro de um loop interrompe a execução na primeira volta, e por que ele deve ficar fora do `for` quando o objetivo é processar todos os itens
- Por que segredos (como `SECRET_KEY`, `FERNET_KEY` e as credenciais do usuário root) não devem ficar no código-fonte, e o papel de variáveis de ambiente (`.env`) nisso
- Boas práticas de segurança básica (nunca logar ou armazenar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Por que uma linha de log/`raise` colocada **depois** de um `return` ou de um `raise` no mesmo bloco nunca é executada (código morto), e por que a ordem das linhas dentro de uma função importa tanto quanto a lógica em si
- Como montar uma mensagem de log de auditoria completa (quem executou, o que fez, em quem, e o resultado), em vez de uma frase genérica que não identifica as partes envolvidas — e por que isso muda dependendo se a rota age sobre o próprio usuário ou sobre outra pessoa
- Separar um modelo Pydantic exclusivo para uma rota de edição parcial (`Optional[str] = None` em todos os campos), em vez de reaproveitar o modelo obrigatório do cadastro — e por que reaproveitar quebraria a validação da rota original
- Pegadinha de comparar uma senha nova com o hash salvo usando `bcrypt.checkpw()` **antes** de sobrescrever esse hash — comparar depois de já ter trocado o valor faz a checagem sempre dar `True`, porque a senha estaria sendo comparada com o hash dela mesma
- Diferença entre usar `try/except` para um erro que o próprio Python pode lançar em tempo de execução e usar `if/raise` para uma condição de negócio que já se sabe checar de antemão (como comparar duas senhas) — e por que todo bloco `try`/`except` precisa ter corpo, nunca ficar vazio
- Quebra de uma condição booleana longa (`and` encadeado) em várias linhas usando parênteses, como alternativa manual quando o `autopep8` não mexe em condições de código
- Diferença entre `W504` (quebra de linha logo depois de um operador lógico, como `and`/`or` deixado no fim da linha) e a convenção adotada de colocar o operador no **início** da linha seguinte — e por que só mover a quebra de linha não resolve nada se o operador continuar na posição errada
- `W291` (espaço em branco sobrando no fim de uma linha) como um erro sutil de deixar passar ao reformatar manualmente uma condição quebrada em várias linhas, e a configuração de editor ("trim trailing whitespace on save") que evita reintroduzi-lo
- Risco de um import "morto" entrar no arquivo sem querer via autocomplete do editor, e como o `flake8` (`F401`) sinaliza isso
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`, `PATCH`, `DELETE`), path parameters e por que cada combinação verbo+path deve representar uma única ação
- Diagnóstico de testes de API por código de status: como a progressão de um erro (404 → 405 → 422 → 200/403) durante o debug aponta, nessa ordem, para "rota não existe" → "método errado" → "corpo da requisição errado" → "lógica de autorização", útil pra saber onde procurar antes mesmo de ler o traceback inteiro
- Diferença entre passar um dicionário Python válido como corpo da requisição (`json={"campo": valor}`) e escrever o nome da classe do modelo Pydantic dentro do dicionário por engano — o nome do modelo é só documentação/validação do lado do servidor, nunca faz parte do JSON enviado
- Por que o atalho `TestClient.delete()` não aceita o argumento `json` (por padrão um DELETE "não deveria" ter corpo), e como usar `client.request("DELETE", ..., json=...)` para contornar isso quando a rota exige dados no corpo
- Uso de `ast.parse()` para isolar rapidamente um `SyntaxError` de um arquivo, sem precisar rodar o pytest inteiro por cima
- O que é um linter e como o `flake8` funciona por baixo dos panos, combinando `pycodestyle` (estilo), `pyflakes` (erros lógicos) e `mccabe` (complexidade) — e por que os códigos de erro têm essa cara (`E501`, `F401`, `C901`)
- Diferença entre configurar um linter (`.flake8`, `max-line-length`, `exclude`) e silenciar um aviso pontual com `# noqa: CÓDIGO` numa linha específica, e por que abusar do `# noqa` é sinal de que a regra deveria mudar globalmente, não ser abafada linha a linha
- Diferença entre erros de **estilo** (linha em branco, espaçamento, comprimento de linha — resolvíveis por formatação automática) e erros de **lógica** (`global` sem uso real, função redefinida — que exigem decisão humana, por isso nenhuma ferramenta de formatação mexe neles sozinha)
- Uso de `autopep8 --aggressive` para corrigir automaticamente a maior parte dos avisos de estilo de um arquivo já escrito, em vez de corrigir um por um manualmente
- Por que `global` só é necessário quando uma variável de módulo é **reatribuída** dentro de uma função (`variavel = novo_valor`), e não quando ela é apenas **mutada** (`variavel[chave] = valor`) — nesse segundo caso a declaração `global` não tem efeito nenhum
- Reconhecer quando duas funções com o mesmo nome no mesmo arquivo (uma sobrescrevendo a outra silenciosamente) é um bug de nomenclatura, mesmo quando o programa continua funcionando sem erro aparente
- `E402` (import fora do topo do arquivo): por que o PEP 8 exige que todo código executável (como instanciar `app = FastAPI()`) venha depois de todos os imports, e não misturado entre eles
- Por que um dado sensível que precisa **sobreviver** a uma operação destrutiva sobre outra estrutura de dados (como limpar um dicionário de usuários) não deve viver dentro dessa mesma estrutura — e como tratar esse dado como um caso especial, verificado antes de qualquer acesso ao dicionário, evita tanto perda de dado quanto `KeyError`
- Por que campos sensíveis como senha nunca devem ser incluídos dentro do payload de um JWT — o token é apenas *assinado*, não *criptografado*, então qualquer pessoa consegue decodificar e ler seu conteúdo sem precisar da `SECRET_KEY`
- O que a claim `exp` representa dentro do payload de um JWT (timestamp Unix) e como `jwt.encode()` aceita um objeto `datetime` e converte automaticamente
- Por que `jwt.decode()` já valida a expiração do token sozinho, lançando `jwt.ExpiredSignatureError` quando o `exp` já passou — sem precisar de nenhuma lógica adicional nas rotas que apenas leem o token
- Diferença entre onde a expiração precisa ser **definida** (nos pontos onde o token é criado, no `/login`) e onde ela é **validada** (automaticamente, em todo `jwt.decode()`), e por que confundir os dois lugares levaria a duplicar lógica desnecessariamente
- Trade-off entre um tempo de expiração curto (mais seguro, porém mais fricção para o usuário) e um tempo longo (mais confortável, porém mais arriscado se o token vazar), e por que uma conta com privilégios elevados (como o root) pode justificar uma expiração mais curta que a de um usuário comum
- Conceito de *access token* vs. *refresh token* como estratégia para equilibrar segurança (tokens de vida curta) com experiência de uso (evitar login repetido)
- Como testar a expiração de um JWT sem depender de tempo real: gerar o token manualmente com uma claim `exp` já no passado (em vez de esperar 30 minutos ou logar de verdade), já que um login normal sempre gera um token válido

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
