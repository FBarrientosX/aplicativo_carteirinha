#!/usr/bin/env python3
"""
Script de debug para verificar problemas com admin
"""

import sys
import os

try:
    print("🔍 Iniciando debug...")
    
    # Verificar se conseguimos importar o Flask
    print("📦 Testando importação do Flask...")
    from flask import Flask
    print("✅ Flask importado com sucesso")
    
    # Verificar se conseguimos importar nossa app
    print("📦 Testando importação da app...")
    from app import create_app, db
    print("✅ App importada com sucesso")
    
    # Tentar criar a app
    print("🚀 Criando aplicação...")
    app = create_app()
    print("✅ Aplicação criada com sucesso")
    
    with app.app_context():
        # Verificar conexão com banco
        print("🗄️ Testando conexão com banco...")
        try:
            db.create_all()
            print("✅ Banco de dados conectado")
        except Exception as e:
            print(f"❌ Erro no banco: {str(e)}")
        
        # Verificar modelos
        print("📋 Testando modelos...")
        from app.models import Plano, Modulo
        
        try:
            planos_count = Plano.query.count()
            print(f"✅ Planos no banco: {planos_count}")
        except Exception as e:
            print(f"❌ Erro ao consultar planos: {str(e)}")
        
        # Verificar formulário
        print("📝 Testando formulário...")
        try:
            from app.forms_admin import NovoCondominioForm
            form = NovoCondominioForm()
            print(f"✅ Formulário criado: {len(form.plano_id.choices)} opções de plano")
        except Exception as e:
            print(f"❌ Erro no formulário: {str(e)}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"❌ Erro geral: {str(e)}")
    import traceback
    traceback.print_exc()
