#!/usr/bin/env python3
"""
Teste simples da aplicação
"""

try:
    print("1. Importando Flask...")
    from flask import Flask
    print("✅ Flask importado")
    
    print("2. Importando create_app...")
    from app import create_app, db
    print("✅ create_app importado")
    
    print("3. Criando aplicação...")
    app = create_app()
    print("✅ Aplicação criada")
    
    print("4. Testando contexto...")
    with app.app_context():
        print("✅ Contexto da aplicação funcionando")
        
        print("5. Testando banco de dados...")
        db.create_all()
        print("✅ Banco de dados OK")
        
        print("6. Testando formulário admin...")
        from app.forms_admin import NovoCondominioForm
        
        # Criar um contexto de request para o formulário
        with app.test_request_context():
            form = NovoCondominioForm()
            print(f"✅ Formulário criado: {len(form.plano_id.choices)} opções de plano")
            
    print("\n🎯 TESTE CONCLUÍDO COM SUCESSO!")
    print("O problema pode estar na configuração do servidor web ou no acesso via navegador.")
    
except Exception as e:
    print(f"❌ ERRO: {str(e)}")
    import traceback
    traceback.print_exc()
