#!/usr/bin/env python3
"""
Script para testar a rota de administração diretamente
"""

from app import create_app, db
from flask import url_for
import requests
import time

def testar_rota():
    """Testar se a rota de novo condomínio funciona"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Testando rota de novo condomínio...")
        
        try:
            # Testar se conseguimos gerar a URL
            url = url_for('admin.novo_condominio')
            print(f"✅ URL gerada: {url}")
            
            # Testar se a rota está registrada
            from app.admin_routes import admin_bp
            print(f"✅ Blueprint admin registrado: {len(admin_bp.deferred_functions)} funções")
            
            # Listar todas as rotas do admin
            print("📋 Rotas disponíveis no admin:")
            for rule in app.url_map.iter_rules():
                if rule.endpoint and rule.endpoint.startswith('admin.'):
                    print(f"  - {rule.endpoint}: {rule.rule}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao testar rota: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def testar_formulario_com_request():
    """Testar formulário dentro de um contexto de request"""
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            print("\n🔍 Testando formulário com contexto de request...")
            
            try:
                from app.forms_admin import NovoCondominioForm
                
                # Simular um request GET
                with client.session_transaction() as sess:
                    sess['_csrf_token'] = 'test-token'
                
                form = NovoCondominioForm()
                print(f"✅ Formulário criado com sucesso!")
                print(f"📝 Opções de plano: {len(form.plano_id.choices)} opções")
                for choice in form.plano_id.choices:
                    print(f"  - {choice}")
                
                return True
                
            except Exception as e:
                print(f"❌ Erro ao criar formulário: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == '__main__':
    print("🚀 Testando sistema de administração...")
    print("=" * 50)
    
    rota_ok = testar_rota()
    form_ok = testar_formulario_com_request()
    
    print("\n" + "=" * 50)
    print("📊 Resultados:")
    print(f"   • Rota OK: {'Sim' if rota_ok else 'Não'}")
    print(f"   • Formulário OK: {'Sim' if form_ok else 'Não'}")
    
    if rota_ok and form_ok:
        print("\n✅ Sistema funcionando! Tente acessar via navegador.")
    else:
        print("\n❌ Ainda há problemas a resolver.")
