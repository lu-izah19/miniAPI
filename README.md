# miniAPI

Projeto de estudo desenvolvido durante o estágio em desenvolvimento back end, com o objetivo de praticar lógica de programação em Python e, na sequência, os fundamentos de desenvolvimento de APIs com **FastAPI**.

O projeto contém duas versões, que representam etapas diferentes do aprendizado:

- **Versão terminal** — um sistema de cadastro, login e perfil de usuário rodando via linha de comando.
- **Versão API** — adaptação do mesmo sistema para rodar como uma API web usando FastAPI, já com todas as rotas migradas para banco de dados real.

## Status

🚧 Em desenvolvimento. A versão terminal está funcional. A versão API já tem rotas próprias por ação, modelos Pydantic separados da classe de estado, salva a senha como hash (`bcrypt`), suporta múltiplos usuários via banco de dados, e o `/login` já gera um token JWT assinado (`SECRET_KEY` guardada em `.env`, fora do código). A rota `/perfil` está protegida por token JWT (`Authorization: Bearer`), sem aceitar o email diretamente na URL, e trata token inválido/expirado com 401. O `/login` também trata email inexistente (404) e senha incorreta (401).

Há autorização por papel (`user`/`admin`): o cadastro define `"user"` por padrão, e o papel **não é informado no login** — o `/login` busca o papel diretamente do cadastro e o inclui dentro do token JWT gerado. A rota `/admin` é restrita a usuários com papel `"admin"` ou ao root (403 para quem não é) e retorna a lista de **todos os usuários cadastrados** (nome e email de cada um), sem expor senha nem papel.

A API cobre um CRUD completo de administração e de autogerenciamento de conta: um admin pode alterar o papel de qualquer usuário, excluir um usuário e resetar a senha de alguém que esqueceu; qualquer usuário logado pode editar o próprio perfil (nome, email e/ou senha, de forma independente) ou desativar a própria conta.

O email do usuário é criptografado em repouso: ele é salvo de forma reversível (`Fernet`, criptografia simétrica), diferente da senha (hash `bcrypt`, irreversível). **Como a criptografia com Fernet não é determinística** (o mesmo email gera um resultado diferente a cada vez que é criptografado), não é possível localizar um usuário no banco com um `WHERE email = %s` comparando o email puro digitado com o valor salvo. A solução adotada, sem alterar a estrutura da tabela, foi trazer todos os usuários (`SELECT` sem `WHERE`) e descriptografar o email de cada linha em um loop, até achar a que bate com o email recebido na requisição — esse padrão se repete em toda rota que precisa localizar um usuário pelo email.

## ✅ Migração para MariaDB (concluída)

O projeto migrou do armazenamento em dicionário (em memória) para um banco de dados **MariaDB** real, usando `mysql.connector` para rodar as queries SQL diretamente (sem ORM). **Todas as rotas de escrita e leitura estão migradas e usando o padrão de busca por loop com descriptografia de email.**

**Rotas migradas e revisadas:**
- `POST /usuario` (cadastro) — `INSERT INTO usuarios` com email criptografado (`Fernet`) e senha em hash `bcrypt`, `commit()`, e tratamento de email duplicado via `except mysql.connector.errors.IntegrityError` (409).
- `POST /login` — busca por loop com descriptografia de email.
- `PATCH /admin/papel` — checagem de permissão feita direto pelo `payload["papel"]` do token (sem busca extra), `UPDATE` usando o email **criptografado** da linha encontrada.
- `GET /admin` — corrigido o bug em que o `return` da listagem estava indentado dentro do `for`, fazendo a rota devolver só o primeiro usuário; agora lista todos corretamente, nos dois branches (root e admin).
- `DELETE /admin/usuario` — migrada para o padrão de busca por loop; corrigida a sintaxe SQL (`DELETE FROM ... WHERE`), o uso do email criptografado no `WHERE`, e a adição do `commit()` que faltava.
- `PATCH /admin/usuario` (reset de senha) — corrigida a busca, que comparava email puro com a coluna criptografada; agora usa o padrão de loop.
- `PATCH /perfil/desativar` — corrigida a busca por email (estava usando um parâmetro inexistente, `dados.email`, em vez do email de quem está logado) e o `WHERE` do `UPDATE`.
- `GET /perfil` — corrigida a busca por email; adicionado tratamento explícito para o caso em que o usuário não é encontrado (404), evitando um erro não tratado quando a conta some do banco com o token ainda válido.
- `PATCH /perfil/usuario` (editar o próprio perfil) — reescrita: os três campos opcionais (nome, senha, email) agora são totalmente independentes entre si, cada alteração tem seu próprio `commit()` e `return`; a checagem de "esse novo email já pertence a outro usuário" foi implementada de fato contra o banco; e foi tratado o caso-limite em que o usuário reenvia o próprio email sem alterá-lo (retorna sucesso sem tentar um update desnecessário).

## 🚧 Reestruturação do projeto (em andamento)

Por orientação da supervisora, o projeto está sendo reorganizado em múltiplos arquivos, seguindo o mesmo padrão usado por outra colega de estágio, em vez de manter tudo em um único `api.py`.

**Nova estrutura:**
- `config.py` — variáveis de ambiente e configurações (chaves, credenciais do banco)
- `database.py` — conexão com o MariaDB
- `models.py` — classes Pydantic e a classe de estado `Usuario`
- `auth.py` — criptografia/descriptografia de email (`Fernet`)
- `main.py` — instância do FastAPI e todas as rotas

O antigo `api.py` monolítico está sendo descontinuado em favor dessa separação por responsabilidade.

A suíte de testes também está sendo dividida por domínio:
- `tests/conftest.py` — cliente de teste e funções auxiliares compartilhadas
- `tests/test_auth.py` — login, token e acesso a rotas protegidas
- `tests/test_admin.py` — permissões e ações administrativas
- `tests/test_perfil.py` — edição do próprio perfil

## Plano para amanhã

1. Resolver a dependência de `usuario_cadastro` nos testes — esse dicionário em memória não existe mais desde a migração para SQL, então a função `limpar_cadastro()` e o import em `conftest.py` precisam de uma nova estratégia de limpeza de dados entre testes (ex: `DELETE`/truncate no banco de teste, ou emails únicos por teste).
2. Confirmar que todos os imports do `main.py`, `config.py`, `database.py`, `models.py` e `auth.py` resolvem sem erro e que a API sobe normalmente com `uvicorn main:app --reload`.
3. Rodar a suíte de testes reorganizada e revisar o que quebrar por causa da reestruturação.
4. Apagar o `api.py` antigo depois de confirmar que `main.py` + módulos substituem ele por completo.
5. Rodar `flake8`/`autopep8` na nova estrutura de arquivos.
6. Atualizar este README com o resultado da reestruturação.

## Funcionalidades

- Cadastro de usuário (nome, email e senha), com papel `"user"` atribuído por padrão — grava no banco com email criptografado
- Login com verificação de credenciais e geração de token JWT contendo o papel do usuário, com expiração de 30 minutos (`exp`)
- Usuário root fixo, definido por variáveis de ambiente e não persistido junto com os demais usuários
- Visualização de perfil do usuário logado, protegida por token JWT
- Edição do próprio perfil (nome, email e/ou senha, todos opcionais e independentes), protegida por token JWT
- Desativação da própria conta (em vez de exclusão), protegida por token JWT
- Rota administrativa (`/admin`), acessível para usuários com papel `"admin"` ou para o root, que lista todos os usuários cadastrados
- Alteração do papel de um usuário por um admin, com checagem de permissão baseada no papel de quem pediu (não do alvo)
- Exclusão de qualquer usuário por um admin
- Reset de senha de qualquer usuário por um admin
- Tratamento de erros HTTP específicos: 404, 401, 403, 409
- Registro de eventos via `logging`, incluindo trilha de auditoria nas ações administrativas
- Criptografia reversível do email em repouso (`Fernet`), com busca por descriptografia em loop (já que Fernet não é determinístico)
- Testes automatizados com `pytest` e `TestClient`, organizados por domínio
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

## Aprendizados do projeto

- Por que criptografia simétrica não-determinística (`Fernet`) impede localizar um registro com um `WHERE coluna = %s` direto: o mesmo email criptografado duas vezes gera dois resultados diferentes, então a busca precisa trazer tudo e comparar após descriptografar, em vez de filtrar no SQL
- Diferença entre a sintaxe de um `INSERT` (`INSERT INTO tabela (colunas) VALUES (valores)`), a de um `UPDATE` (`SET coluna = valor WHERE`) e a de um `DELETE` (`DELETE FROM tabela WHERE`) — misturar `SET` num `DELETE`, por exemplo, gera um erro de sintaxe
- Por que a ordem dos valores numa tupla de parâmetros precisa bater exatamente com a ordem das colunas listadas na query — inverter a ordem grava os dados nos campos errados, sem erro nenhum sendo levantado
- Risco de um `except:` genérico (sem tipo especificado) mascarar qualquer erro, não só o esperado — e por que capturar o tipo específico (`mysql.connector.errors.IntegrityError`) é mais seguro
- Diferença entre `.encode()` e `.decode()`: só bytes têm `.decode()`, só strings têm `.encode()` — confundir os dois estoura `AttributeError`
- Risco de segurança de checar permissão de admin usando os dados do usuário **alvo** de uma ação em vez dos dados de quem **fez a requisição** — a diferença entre validar credenciais de quem pediu (`payload`) e credenciais de quem vai sofrer a ação (`dados`)
- Por que um `return` colocado dentro de um `for` (em vez de depois dele) interrompe o loop na primeira volta — fazendo uma listagem devolver só o primeiro item, mesmo sem erro nenhum aparecer
- Diferença entre acessar um campo de um dicionário (`usuario["campo"]`) e de um objeto (`usuario.campo`) — o resultado de `cursor.fetchone()`/`fetchall()` (com `dictionary=True`) nunca tem atributos, só chaves
- Por que uma variável de resultado de uma busca anterior (tipo `usuario`, resultado de um `SELECT` feito antes do `UPDATE`) não se atualiza sozinha depois que o `UPDATE` roda — devolver o "valor antigo" em vez do valor que acabou de ser salvo
- Diferença entre inicializar uma variável de controle com `None` (ausência real de valor, testável com `is not None`) e usar uma string como `"None"` ou um número como placeholder — só o `None` verdadeiro do Python evita erros ao tentar tratar essa variável como se fosse sempre um dicionário encontrado
- Por que múltiplos `if` independentes, cada um terminando em `return`, garantem que campos opcionais de uma rota (nome, senha, email) sejam realmente tratados de forma isolada — sem um cobrir ou pular o outro por engano
- Diferença entre reatribuir a mesma variável para dois propósitos diferentes (ex: usar `usuario` tanto para "quem está logado" quanto para "quem já tem esse email") e usar duas variáveis com nomes distintos — reaproveitar o nome apaga a referência anterior antes dela ser usada
- Uma função Python que termina sem bater em nenhum `return` explícito devolve `None` silenciosamente — o que pode fazer uma API responder "sucesso" vazio quando na real nada foi processado

## Versão terminal

Sistema com menu interativo no terminal, controlado por um loop `while True` com estrutura `if/elif/else`. Os dados do usuário são armazenados em memória durante a execução (sem persistência em banco de dados).

### Como rodar

```bash
python terminal.py
```

## Versão API

### Rotas definidas até o momento

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Rota inicial, mensagem de boas-vindas |
| `POST` | `/usuario` | Cadastro de novo usuário. ✅ |
| `POST` | `/login` | Login do usuário ou do root. ✅ |
| `GET` | `/perfil` | Visualização de perfil do usuário logado. ✅ |
| `PATCH` | `/perfil/usuario` | Edição do próprio perfil (nome, email e/ou senha, independentes). ✅ |
| `PATCH` | `/perfil/desativar` | Desativação da própria conta. ✅ |
| `GET` | `/admin` | Lista todos os usuários cadastrados. ✅ |
| `PATCH` | `/admin/papel` | Altera o papel de um usuário. ✅ |
| `DELETE` | `/admin/usuario` | Exclui um usuário. ✅ |
| `PATCH` | `/admin/usuario` | Reseta a senha de um usuário. ✅ |

### Configuração necessária

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
uvicorn main:app --reload
```

## Testes automatizados

> ⚠️ Nota: a suíte de testes ainda foi escrita contra a versão em dicionário da API e depende de `usuario_cadastro`, que não existe mais desde a migração para MariaDB. Precisa de revisão antes de rodar contra o `main.py` atual — item prioritário do próximo dia de trabalho.

```bash
pytest
```

## Qualidade de código (lint)

```bash
pip install flake8
flake8 main.py config.py database.py models.py auth.py
```

## Autora

Luiza Souza ([@lu-izah19](https://github.com/lu-izah19))
