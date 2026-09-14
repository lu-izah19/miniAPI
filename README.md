# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** *(em andamento)* — adaptação do mesmo sistema para rodar como uma API web usando FastAPI.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), migrou o armazenamento para múltiplos usuários, e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). A rota `/perfil` já está protegida por token JWT (`Authorization: Bearer`), sem mais aceitar o email diretamente na URL, e trata token inválido/expirado com 401. O `/login` também trata email inexistente (404) e senha incorreta (401).

Foi adicionada autorização por papel (`user`/`admin`): o cadastro define `"user"` por padrão, e o papel **não é mais informado no login** — o `/login` busca o papel diretamente do cadastro e o inclui dentro do token JWT gerado. A rota `/admin` é restrita a usuários com papel `"admin"` ou ao root (403 para quem não é) e retorna a lista de **todos os usuários cadastrados** (nome e email de cada um), sem expor senha nem papel.

A API cobre um CRUD mais completo de administração e de autogerenciamento de conta: um admin pode alterar o papel de qualquer usuário, excluir um usuário e resetar a senha de alguém que esqueceu; qualquer usuário logado pode editar o próprio perfil (nome, email e senha) ou desativar a própria conta.

O email do usuário é criptografado em repouso: ele é salvo de forma reversível (`Fernet`, criptografia simétrica), diferente da senha (hash `bcrypt`, irreversível). **Como a criptografia com Fernet não é determinística** (o mesmo email gera um resultado diferente a cada vez que é criptografado), não é possível localizar um usuário no banco com um `WHERE email = %s` comparando o email puro digitado com o valor salvo. A solução adotada, sem alterar a estrutura da tabela, foi trazer todos os usuários (`SELECT` sem `WHERE`) e descriptografar o email de cada linha em um loop, até achar a que bate com o email recebido na requisição — esse padrão se repete em toda rota que precisa localizar um usuário pelo email.

## 🚧 Migração para MariaDB (em andamento)

O projeto está migrando do armazenamento em dicionário (em memória) para um banco de dados **MariaDB** real, usando `mysql.connector` para rodar as queries SQL diretamente (sem ORM).

**Rotas migradas e funcionando:**
- `POST /usuario` (cadastro) — `INSERT INTO usuarios` com email criptografado (`Fernet`) e senha em hash `bcrypt`, `commit()`, e tratamento de email duplicado via `except mysql.connector.errors.IntegrityError` (409). Estrutura da tabela mantida sem alterações.
- `POST /login` — reescrito hoje: como o email agora é salvo criptografado, a busca traz todos os usuários e descriptografa cada um até achar o que bate com o email informado no login.
- `PATCH /admin/papel` — migrado hoje: checagem de permissão feita direto pelo `payload["papel"]` do token (sem busca extra), correção de uma falha de segurança em que a checagem de admin estava olhando pro papel do usuário-alvo em vez de quem fez a requisição, e `UPDATE` usando o email **criptografado** da linha encontrada no `WHERE` (não o email puro do corpo da requisição).

**Migrada hoje, com um ajuste pendente:**
- `GET /admin` — reescrita com o mesmo padrão de busca por loop. Um bug foi identificado: o `return` da listagem estava indentado *dentro* do `for`, fazendo a rota devolver só o primeiro usuário da lista em vez de todos. A correção (desindentar o `return` pra fora do loop) foi identificada mas ainda **não foi reaplicada no arquivo** — primeira coisa a confirmar amanhã.

**Descoberta de hoje — revisar amanhã:** três rotas dadas como "migradas" antes de hoje na verdade ainda buscam o usuário com `WHERE email = %s` comparando com o email **puro**, mas a coluna do banco guarda o email **criptografado** desde que o cadastro foi migrado. Isso quer dizer que, hoje, essas rotas não encontram ninguém na prática:
- `PATCH /admin/usuario` (reset de senha)
- `PATCH /perfil/desativar`
- `GET /perfil`

Todas precisam ser reescritas com o mesmo padrão de busca por loop (`SELECT` sem `WHERE` + descriptografar até achar o match) usado em `/login`, `/admin` e `/admin/papel`.

**Em migração, com bugs conhecidos:**
- `PATCH /perfil/usuario` (editar o próprio perfil) — além do problema de busca por email acima, os três campos opcionais (nome, senha, email) ainda não são totalmente independentes: alterar só o nome (sem senha) não salva nem confirma sucesso; alterar a senha sem trocar o email não executa o `commit()`. A checagem de "esse novo email já pertence a outro usuário" também ainda não foi implementada de fato no banco.

**Ainda não migrada** (continua com a lógica antiga de dicionário, que não funciona mais contra o banco):
- `DELETE /admin/usuario`

## Plano para amanhã

1. Aplicar a correção do `return` dentro do loop em `GET /admin`.
2. Migrar `DELETE /admin/usuario` pro padrão de busca por loop (duas buscas separadas: quem pediu vs. quem é o alvo).
3. Corrigir `PATCH /admin/usuario`, `PATCH /perfil/desativar` e `GET /perfil` pra usar o mesmo padrão de busca por loop, em vez do `WHERE email = %s` direto.
4. Fechar a migração de `PATCH /perfil/usuario` (busca por loop + independência real dos três campos opcionais + checagem de email duplicado).
5. Rodar `autopep8` de novo no arquivo inteiro, já que a indentação ficou inconsistente durante a migração manual.
6. Revisar a suíte de testes (`pytest`) contra as rotas migradas — a suíte atual ainda foi escrita pra versão em dicionário.

## Funcionalidades

- Cadastro de usuário (nome, email e senha), com papel `"user"` atribuído por padrão — grava no banco com email criptografado
- Login com verificação de credenciais e geração de token JWT contendo o papel do usuário, com expiração de 30 minutos (`exp`)
- Usuário root fixo, definido por variáveis de ambiente e não persistido junto com os demais usuários
- Visualização de perfil do usuário logado, protegida por token JWT
- Edição do próprio perfil (nome, email e/ou senha, todos opcionais), protegida por token JWT *(em migração)*
- Desativação da própria conta (em vez de exclusão), protegida por token JWT *(precisa de ajuste na busca por email)*
- Rota administrativa (`/admin`), acessível para usuários com papel `"admin"` ou para o root, que lista todos os usuários cadastrados
- Alteração do papel de um usuário por um admin, com checagem de permissão baseada no papel de quem pediu (não do alvo)
- Exclusão de qualquer usuário por um admin *(ainda não migrada)*
- Reset de senha de qualquer usuário por um admin *(precisa de ajuste na busca por email)*
- Tratamento de erros HTTP específicos: 404, 401, 403, 409
- Registro de eventos via `logging`, incluindo trilha de auditoria nas ações administrativas
- Criptografia reversível do email em repouso (`Fernet`), com busca por descriptografia em loop (já que Fernet não é determinístico)
- Testes automatizados com `pytest` e `TestClient`
- Padrão de estilo verificado por `flake8`

## Tecnologias utilizadas

- Python 3
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [bcrypt](https://pypi.org/project/bcrypt/)
- [PyJWT](https://pyjwt.readthedocs.io/)
- [cryptography](https://cryptography.io/) *(Fernet)*
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [mysql-connector-python](https://pypi.org/project/mysql-connector-python/)
- Módulo `datetime` da biblioteca padrão
- [pytest](https://docs.pytest.org/)
- [httpx](https://www.python-httpx.org/)
- [flake8](https://flake8.pycqa.org/)
- [autopep8](https://pypi.org/project/autopep8/)
- Módulo `logging` da biblioteca padrão

## Aprendizados do projeto (novos, de hoje)

- Por que criptografia simétrica não-determinística (`Fernet`) impede localizar um registro com um `WHERE coluna = %s` direto: o mesmo email criptografado duas vezes gera dois resultados diferentes, então a busca precisa trazer tudo e comparar após descriptografar, em vez de filtrar no SQL
- Diferença entre a sintaxe de um `INSERT` (`INSERT INTO tabela (colunas) VALUES (valores)`) e a de um `UPDATE`/`DELETE` (`WHERE` pra filtrar) — usar `WHERE` num `INSERT` não tem efeito nenhum, porque não existe linha nenhuma ainda pra filtrar
- Por que a ordem dos valores numa tupla de parâmetros precisa bater exatamente com a ordem das colunas listadas na query — inverter a ordem grava os dados nos campos errados, sem erro nenhum sendo levantado
- Risco de um `except:` genérico (sem tipo especificado) mascarar qualquer erro, não só o esperado — e por que capturar o tipo específico (`mysql.connector.errors.IntegrityError`) é mais seguro
- Diferença entre `.encode()` e `.decode()`: só bytes têm `.decode()`, só strings têm `.encode()` — confundir os dois estoura `AttributeError`
- Risco de segurança de checar permissão de admin usando os dados do usuário **alvo** de uma ação em vez dos dados de quem **fez a requisição** — a diferença entre validar credenciais de quem pediu (`payload`) e credenciais de quem vai sofrer a ação (`dados`)
- Por que um `return` colocado dentro de um `for` (em vez de depois dele) interrompe o loop na primeira volta — fazendo uma listagem devolver só o primeiro item, mesmo sem erro nenhum aparecer
- Diferença entre acessar um campo de um dicionário (`usuario["campo"]`) e de um objeto (`usuario.campo`) — o resultado de `cursor.fetchone()`/`fetchall()` (com `dictionary=True`) nunca tem atributos, só chaves
- Por que uma variável de resultado de uma busca anterior (tipo `usuario`, resultado de um `SELECT` feito antes do `UPDATE`) não se atualiza sozinha depois que o `UPDATE` roda — devolver o "valor antigo" em vez do valor que acabou de ser salvo

## Versão terminal

Sistema com menu interativo no terminal, controlado por um loop `while True` com estrutura `if/elif/else`. Os dados do usuário são armazenados em memória durante a execução (sem persistência em banco de dados).

### Como rodar

```bash
python terminal.py
```

## Versão API *(em andamento)*

### Rotas definidas até o momento

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Rota inicial, mensagem de boas-vindas |
| `POST` | `/usuario` | Cadastro de novo usuário. ✅ Migrado para SQL |
| `POST` | `/login` | Login do usuário ou do root. ✅ Migrado para SQL |
| `GET` | `/perfil` | Visualização de perfil do usuário logado. ⚠️ Busca por email precisa de ajuste |
| `PATCH` | `/perfil/usuario` | Edição do próprio perfil. ⚠️ Em migração, com bugs conhecidos |
| `PATCH` | `/perfil/desativar` | Desativação da própria conta. ⚠️ Busca por email precisa de ajuste |
| `GET` | `/admin` | Lista todos os usuários cadastrados. ⚠️ Migrada, falta reaplicar correção de um bug |
| `PATCH` | `/admin/papel` | Altera o papel de um usuário. ✅ Migrado para SQL |
| `DELETE` | `/admin/usuario` | Exclui um usuário. ⚠️ Ainda não migrada para SQL |
| `PATCH` | `/admin/usuario` | Reseta a senha de um usuário. ⚠️ Busca por email precisa de ajuste |

### Configuração necessária

SECRET_KEY=<string aleatória gerada com secrets.token_hex(32)>
FERNET_KEY=<chave gerada com Fernet.generate_key()>
USUARIO_ROOT=<nome de exibição do usuário root>
SENHA_ROOT=<senha do usuário root>
EMAIL_ROOT=<email do usuário root>
MARIADB_USER=<usuário do banco MariaDB>
MARIADB_PASSWORD=<senha do banco MariaDB>
MARIADB_DATABASE=<nome do banco MariaDB>


### Como rodar

```bash
uvicorn api:app --reload
```

## Testes automatizados

> ⚠️ Nota: a suíte de testes ainda foi escrita contra a versão em dicionário da API. Com a migração para MariaDB em andamento, precisa de revisão assim que as rotas restantes forem migradas.

## Qualidade de código (lint)

```bash
pip install flake8
flake8 api.py
```

> Nota: o código tem indentação inconsistente em trechos recém-migrados; rodar `autopep8` de novo quando as rotas restantes forem migradas.

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
