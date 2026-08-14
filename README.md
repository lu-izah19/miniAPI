# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), migrou o armazenamento para múltiplos usuários (dicionário indexado por email), e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). A rota `/perfil` já está protegida por token JWT (`Authorization: Bearer`), sem mais aceitar o email diretamente na URL, e trata token inválido/expirado com 401. O `/login` também trata email inexistente (404) e senha incorreta (401).

Foi adicionada autorização por papel (`user`/`admin`): o cadastro define `"user"` por padrão, e o papel **não é mais informado no login** — o `/login` busca o papel diretamente do cadastro e o inclui dentro do token JWT gerado, já que essa informação já existe desde o cadastro e não faz sentido pedir de novo. A rota `/admin` é restrita a usuários com papel `"admin"` (403 para quem não é) e tem conteúdo próprio: retorna a lista de **todos os usuários cadastrados** (nome e email de cada um), sem expor senha nem papel.

A API agora também cobre um CRUD mais completo de administração e de autogerenciamento de conta: um admin pode alterar o papel de qualquer usuário, excluir um usuário e resetar a senha de alguém que esqueceu; qualquer usuário logado pode editar o próprio perfil (nome, email e senha) ou deletar a própria conta. O tratamento de exceções de token também ficou mais específico: em vez de um `except:` genérico (que podia "engolir" até um `HTTPException` de 403 lançado dentro do mesmo `try`), agora cada rota protegida usa `except jwt.ExpiredSignatureError` e `except jwt.InvalidTokenError` separados, e a lógica de autorização (checar papel) ficou fora do bloco `try`, garantindo que 401 (token inválido) e 403 (sem permissão) nunca se confundam.

## Funcionalidades

- Cadastro de usuário (nome, email e senha), com papel `"user"` atribuído por padrão
- Login com verificação de credenciais e geração de token JWT contendo o papel do usuário (obtido do cadastro, não informado no login)
- Visualização de perfil do usuário logado, protegida por token JWT
- Edição do próprio perfil (nome, email e senha), protegida por token JWT, com verificação de conflito de email
- Exclusão da própria conta, protegida por token JWT
- Rota administrativa (`/admin`), acessível apenas para usuários com papel `"admin"`, que lista todos os usuários cadastrados (nome e email, sem senha)
- Alteração do papel de um usuário por um admin, sem precisar editar o dicionário manualmente
- Exclusão de qualquer usuário por um admin
- Reset de senha de qualquer usuário por um admin (fluxo de "esqueci minha senha")
- Tratamento de erros HTTP específicos: 404 (usuário não encontrado), 401 (senha, token inválido ou expirado), 403 (sem permissão de admin), 409 (email já em uso)
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
| `PATCH` | `/perfil/usuario` | Edição do próprio perfil (nome, email e senha), protegida por token JWT. O usuário editado é sempre o dono do token (nunca um email vindo do corpo). 409 se o novo email já pertencer a outro usuário |
| `DELETE` | `/perfil/usuario` | Exclusão da própria conta, protegida por token JWT. Não recebe nada no corpo — o usuário deletado é sempre o dono do token |
| `GET` | `/admin` | Rota administrativa, protegida por token JWT e restrita a usuários com papel `"admin"`. Retorna a lista de todos os usuários cadastrados (nome e email, sem senha). 401 se o token for inválido/expirado, 403 se o usuário não for admin |
| `PATCH` | `/admin/papel` | Altera o papel (`user`/`admin`) de um usuário especificado por email. Restrita a admins. 404 se o email não existir, 403 se quem chama não for admin |
| `DELETE` | `/admin/usuario` | Exclui um usuário especificado por email. Restrita a admins. 404 se o email não existir, 403 se quem chama não for admin |
| `PATCH` | `/admin/usuario` | Reseta a senha de um usuário especificado por email (fluxo de "esqueci minha senha"). Restrita a admins. 404 se o email não existir, 403 se quem chama não for admin |

> Cada ação tem seu próprio path, o que resolveu o conflito de rotas duplicadas que existia quando `cadastro`, `login` e `perfil` disputavam o mesmo endereço.

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

- [ ] Criptografar dados sensíveis do usuário (ex: email) em repouso, com criptografia reversível (diferente do hash da senha, que nunca precisa ser lido de volta)
- [ ] Decidir se vale manter a rota `GET /usuario`, já que hoje ela só retorna uma mensagem
- [ ] Revisar/redocumentar no README o trade-off entre incluir o papel no payload do token vs. consultar sempre a fonte de dados — considerando o que fazer se o papel de um usuário logado mudar antes do token expirar

### Resolvido recentemente

- [x] Adicionada a rota `PATCH /admin/usuario` para reset de senha de um usuário por um admin (fluxo "esqueci minha senha"), usando um modelo próprio (`UsuarioSenha`, só com `email` e `senha`) em vez de reaproveitar um modelo com campos desnecessários
- [x] Adicionada a rota `DELETE /perfil/usuario`, para o próprio usuário deletar a conta, usando somente o email do token (sem receber nada no corpo da requisição)
- [x] Adicionada a rota `PATCH /perfil/usuario`, para o próprio usuário editar nome, email e senha, buscando o usuário sempre pelo email do token (nunca por um email vindo do corpo, para não permitir editar a conta de outra pessoa)
- [x] Tratada a troca de email na edição de perfil: como `usuario_cadastro` é indexado por email, ao mudar o email é preciso mover o registro para a nova chave e apagar a antiga, além de checar conflito (409) se o novo email já pertencer a outro usuário
- [x] Adicionada a rota `DELETE /admin/usuario`, para um admin excluir qualquer usuário por email, usando um modelo próprio (`UsuarioDelete`, só com `email`)
- [x] Adicionada a rota `PATCH /admin/papel`, para um admin alterar o papel de qualquer usuário por email, sem precisar mais editar o dicionário manualmente
- [x] Corrigido `cadastro()` para salvar o nome real enviado na requisição (`dados.nome`), em vez de forçar `nome=None`
- [x] Corrigido o `except:` genérico do `/admin` e do `/perfil`, que capturava até o `HTTPException(403)` lançado dentro do próprio `try` e devolvia 401 no lugar. Agora o `try` cuida só do `jwt.decode`, com `except jwt.ExpiredSignatureError` e `except jwt.InvalidTokenError` específicos, e a checagem de papel/autorização fica fora do `try`
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
- [x] Criados modelos Pydantic (`UsuarioCadastro`, `UsuarioInicio`, `UsuarioLogin`, `UsuarioPerfil`, `UsuarioDelete`, `UsuarioSenha`) separados da classe `Usuario`, que guarda o estado em memória
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
- Diferença entre `except` genérico e `except` específico por tipo de exceção (`jwt.ExpiredSignatureError`, `jwt.InvalidTokenError`), incluindo a ordem de precedência quando uma exceção é subclasse de outra, e o risco de um `except` genérico capturar até um `HTTPException` lançado dentro do próprio `try`
- Diferença entre `raise` (interrompe a execução e propaga um erro) e `return` (devolve um valor normalmente)
- Uso de `HTTPException` para devolver códigos de status HTTP apropriados a cada tipo de falha (404, 401, 403, 409), em vez de mensagens de erro genéricas com status 200
- Diferença entre os códigos 401 (não autenticado), 403 (autenticado, mas sem permissão) e 409 (conflito de dado, como email duplicado)
- Controle de acesso baseado em papel (role-based access control): por que o papel de um usuário deve ser definido no cadastro (pela aplicação) e nunca escolhido livremente pelo próprio usuário
- Diferença entre uma ação sobre "si mesmo" (identificar o usuário pelo email do token) e uma ação de admin sobre "outra pessoa" (identificar o usuário-alvo por um email recebido no corpo da requisição)
- `KeyError` ao acessar uma chave inexistente em um dicionário, e por que checar a existência da chave antes (`if chave in dicionario`) evita esse erro
- `del` para remover uma entrada de um dicionário
- Por que, num dicionário indexado por email, alterar apenas o atributo `.email` de um objeto não move o registro — é preciso criar a entrada na nova chave e apagar a antiga — e por que é necessário checar conflito de email antes de permitir a troca
- Como percorrer um dicionário com `for` para acumular resultados em uma lista com `.append()`, e por que declarar a lista **antes** do loop (não dentro dele) é essencial para não perder os dados de cada volta
- Por que um `return` dentro de um loop interrompe a execução na primeira volta, e por que ele deve ficar fora do `for` quando o objetivo é processar todos os itens
- Por que segredos (como a `SECRET_KEY`) não devem ficar no código-fonte, e o papel de variáveis de ambiente (`.env`) nisso
- Boas práticas de segurança básica (nunca logar ou armazenar senhas em texto puro)
- Níveis de log (`INFO`, `WARNING`) e configuração do módulo `logging`
- Fundamentos de APIs REST: rotas, métodos HTTP (`GET`, `POST`, `PATCH`, `DELETE`), path parameters e por que cada combinação verbo+path deve representar uma única ação

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
