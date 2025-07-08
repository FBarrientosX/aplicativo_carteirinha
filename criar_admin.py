from app import create_app, db
from app.models import Usuario, Condominio, ConfiguracaoSistema

app = create_app()

with app.app_context():
    # Criar todas as tabelas
    db.create_all()
    print("✅ Tabelas criadas!")
    
    # Criar condomínio padrão se não existir
    if not Condominio.query.first():
        condominio = Condominio(
            nome='Meu Condomínio',
            endereco='Configure o endereço nas configurações',
            email_administracao='admin@condominio.com',
            telefone='(11) 3333-4444',
            whatsapp='(11) 99999-9999',
            horario_funcionamento='Segunda a Sexta, 8h às 18h',
            dias_aviso_vencimento=30,
            meses_validade_padrao=12,
            permitir_dependentes=True,
            cor_primaria='#007bff',
            cor_secundaria='#6c757d'
        )
        db.session.add(condominio)
        print("✅ Condomínio criado!")
    
    # Criar usuário admin se não existir
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            username='admin',
            email='admin@condominio.com',
            nome_completo='Administrador do Sistema',
            tipo_usuario='admin',
            ativo=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Usuário admin criado!")
    
    # Criar configuração padrão se não existir
    if not ConfiguracaoSistema.query.first():
        config = ConfiguracaoSistema(
            chave='NOME_SISTEMA',
            valor='Sistema de Carteirinhas',
            descricao='Nome do sistema',
            tipo='texto',
            categoria='geral'
        )
        db.session.add(config)
        print("✅ Configuração inicial criada!")
    
    db.session.commit()
    print("\n🎉 Sistema inicializado com sucesso!")
    print("📋 Credenciais:")
    print("   Usuário: admin")
    print("   Senha: admin123") 