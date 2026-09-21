from typing import Optional
from pydantic import BaseModel


class Usuario:
    def __init__(self, nome=None, email=None, senha=None, papel="user"):
        self.nome = nome
        self.email = email
        self.senha = senha
        self.papel = papel


class UsuarioCadastro(BaseModel):
    nome: str
    email: str
    senha: str


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class AlterarPapel(BaseModel):
    email: str
    papel: str


class UsuarioDelete(BaseModel):
    email: str


class UsuarioSenha(BaseModel):
    email: str
    senha: str


class UsuarioAlterarPerfil(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    senha: Optional[str] = None
