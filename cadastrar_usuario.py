#!/usr/bin/env python3
"""
Script para cadastrar novos usuários no sistema
Execute: python3.10 cadastrar_usuario.py
"""

import os
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cadastrar_usuario():
    """Cadastra um novo usuário no sistema"""
    
    try:
        # Conectar ao banco SQLite
        conn = sqlite3.connect('carteirinha_piscina.db')
        cursor = conn.cursor()
        
        print("👤 CADASTRO DE NOVO USUÁRIO")
        print("=" * 40)
        
        # Coletar dados do usuário
        nome_completo = input("Nome completo: ")
        username = input("Username (login): ")
        email = input("Email: ")
        senha = input("Senha: ")
        
        print("\nTipos de usuário disponíveis:")
        print("1. admin - Administrador completo")
        print("2. salva_vidas - Salva-vidas da piscina")
        print("3. super_admin - Super administrador")
        
        tipo_escolha = input("Escolha o tipo (1, 2 ou 3): ")
        
        tipos = {
            '1': 'admin',
            '2': 'salva_vidas', 
            '3': 'super_admin'
        }
        
        tipo_usuario = tipos.get(tipo_escolha, 'admin')
        
        # Verificar se username já existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            print("❌ ERRO: Username já existe!")
            return False
        
        # Verificar se email já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone():
            print("❌ ERRO: Email já existe!")
            return False
        
        # Gerar hash da senha
        password_hash = generate_password_hash(senha)
        
        # Definir tenant_id (1 para o tenant padrão)
        tenant_id = 1 if tipo_usuario != 'super_admin' else None
        
        # Inserir usuário
        cursor.execute("""
            INSERT INTO usuarios (username, nome_completo, email, password_hash, 
                                tipo_usuario, tenant_id, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            nome_completo,
            email,
            password_hash,
            tipo_usuario,
            tenant_id,
            True,
            datetime.now()
        ))
        
        user_id = cursor.lastrowid
        
        # Commit das mudanças
        conn.commit()
        conn.close()
        
        print("\n✅ USUÁRIO CADASTRADO COM SUCESSO!")
        print("=" * 40)
        print(f"👤 Nome: {nome_completo}")
        print(f"🔑 Username: {username}")
        print(f"📧 Email: {email}")
        print(f"🔒 Senha: {senha}")
        print(f"👑 Tipo: {tipo_usuario}")
        print(f"🆔 ID: {user_id}")
        print("\n🌐 Login em: https://barrientos.pythonanywhere.com")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

def listar_usuarios():
    """Lista todos os usuários cadastrados"""
    
    try:
        conn = sqlite3.connect('carteirinha_piscina.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, nome_completo, email, tipo_usuario, ativo FROM usuarios")
        usuarios = cursor.fetchall()
        
        print("\n👥 USUÁRIOS CADASTRADOS:")
        print("=" * 60)
        
        for usuario in usuarios:
            status = "🟢 Ativo" if usuario[4] else "🔴 Inativo"
            print(f"👤 {usuario[1]}")
            print(f"   🔑 Username: {usuario[0]}")
            print(f"   📧 Email: {usuario[2]}")
            print(f"   👑 Tipo: {usuario[3]}")
            print(f"   {status}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    
    while True:
        print("\n🔧 GERENCIADOR DE USUÁRIOS")
        print("=" * 30)
        print("1. Cadastrar novo usuário")
        print("2. Listar usuários existentes")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            cadastrar_usuario()
        elif opcao == '2':
            listar_usuarios()
        elif opcao == '3':
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == '__main__':
    main() 