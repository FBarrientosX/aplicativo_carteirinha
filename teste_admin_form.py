#!/usr/bin/env python3
"""
Script para testar o formulário de administração
"""

from app import create_app, db
from app.models import Plano, Modulo
from app.forms_admin import NovoCondominioForm

def testar_formulario():
    """Testar se o formulário pode ser criado"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Testando criação do formulário...")
        
        try:
            # Verificar planos
            planos = Plano.query.all()
            print(f"📋 Planos encontrados: {len(planos)}")
            for plano in planos:
                print(f"  - {plano.nome} (ID: {plano.id}, Ativo: {plano.ativo}, Público: {plano.publico})")
            
            # Tentar criar o formulário
            form = NovoCondominioForm()
            print(f"✅ Formulário criado com sucesso!")
            print(f"📝 Opções de plano: {form.plano_id.choices}")
            
        except Exception as e:
            print(f"❌ Erro ao criar formulário: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    testar_formulario()
