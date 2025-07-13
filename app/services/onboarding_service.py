# Serviço de onboarding para novos clientes SaaS
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.email_service import EmailService
import secrets
import string

class OnboardingService:
    """Serviço para cadastro e configuração inicial de novos clientes"""
    
    @staticmethod
    def criar_novo_tenant(dados_cliente):
        """
        Cria novo tenant com dados iniciais
        
        Args:
            dados_cliente (dict): Dados do cliente
                - nome: Nome do condomínio
                - subdominio: Subdomínio desejado
                - email: Email do responsável
                - nome_responsavel: Nome do responsável
                - telefone: Telefone
                - cnpj: CNPJ (opcional)
                - senha: Senha inicial
                - plano_id: ID do plano escolhido
        
        Returns:
            tuple: (tenant, admin_user, success_message)
        """
        # Importar aqui para evitar circular imports
        from app.models import Tenant, Usuario, Plano
        
        try:
            # Validar se subdomínio está disponível
            if Tenant.query.filter_by(subdominio=dados_cliente['subdominio']).first():
                raise ValueError(f"Subdomínio '{dados_cliente['subdominio']}' já está em uso")
            
            # Verificar se plano existe
            plano = Plano.query.get(dados_cliente['plano_id'])
            if not plano:
                raise ValueError("Plano não encontrado")
            
            # Criar tenant
            tenant = Tenant(
                nome=dados_cliente['nome'],
                subdominio=dados_cliente['subdominio'],
                email_responsavel=dados_cliente['email'],
                telefone=dados_cliente.get('telefone'),
                cnpj=dados_cliente.get('cnpj'),
                plano_id=dados_cliente['plano_id'],
                data_inicio=datetime.now().date(),
                data_vencimento=datetime.now().date() + timedelta(days=30),  # 30 dias grátis
                status='ativo'
            )
            
            db.session.add(tenant)
            db.session.flush()  # Para obter o ID do tenant
            
            # Criar usuário administrador
            admin = Usuario(
                username=dados_cliente['email'],
                email=dados_cliente['email'],
                nome_completo=dados_cliente['nome_responsavel'],
                tipo_usuario='admin',
                tenant_id=tenant.id,
                permissoes={
                    'admin_tenant': True,
                    'criar_morador': True,
                    'editar_morador': True,
                    'excluir_morador': True,
                    'validar_carteirinha': True,
                    'gerar_carteirinha': True,
                    'ver_relatorios': True,
                    'exportar_dados': True,
                    'configurar_sistema': True,
                    'gerenciar_usuarios': True
                }
            )
            admin.set_password(dados_cliente['senha'])
            
            db.session.add(admin)
            db.session.commit()
            
            # Configurar configurações iniciais
            OnboardingService.configurar_tenant_inicial(tenant.id)
            
            # Enviar email de boas-vindas
            OnboardingService.enviar_boas_vindas(tenant, admin)
            
            return tenant, admin, "Conta criada com sucesso!"
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def configurar_tenant_inicial(tenant_id):
        """Configurar configurações iniciais do tenant"""
        from app.models import ConfiguracaoTenant
        
        configuracoes_iniciais = [
            # Email
            ('email', 'servidor_smtp', 'smtp.gmail.com', 'texto'),
            ('email', 'porta_smtp', '587', 'numero'),
            ('email', 'usar_tls', 'true', 'booleano'),
            ('email', 'remetente_padrao', '', 'email'),
            
            # Carteirinhas
            ('carteirinhas', 'validade_padrao_meses', '12', 'numero'),
            ('carteirinhas', 'aviso_vencimento_dias', '30', 'numero'),
            ('carteirinhas', 'permitir_dependentes', 'true', 'booleano'),
            
            # Sistema
            ('sistema', 'nome_sistema', 'Sistema de Carteirinhas', 'texto'),
            ('sistema', 'timezone', 'America/Sao_Paulo', 'texto'),
            ('sistema', 'idioma', 'pt-BR', 'texto'),
            
            # Notificações
            ('notificacoes', 'enviar_boas_vindas', 'true', 'booleano'),
            ('notificacoes', 'enviar_30_dias', 'true', 'booleano'),
            ('notificacoes', 'enviar_vencimento', 'true', 'booleano'),
        ]
        
        for categoria, chave, valor, tipo in configuracoes_iniciais:
            ConfiguracaoTenant.set_valor(
                tenant_id=tenant_id,
                categoria=categoria,
                chave=chave,
                valor=valor,
                tipo=tipo
            )
    
    @staticmethod
    def enviar_boas_vindas(tenant, admin):
        """Envia email de boas-vindas com instruções"""
        try:
            assunto = f"Bem-vindo ao Sistema de Carteirinhas - {tenant.nome}"
            
            # URL de acesso
            url_acesso = tenant.get_url_sistema()
            
            corpo_email = f"""
            Olá {admin.nome_completo},
            
            Seja bem-vindo ao Sistema de Carteirinhas!
            
            Sua conta foi criada com sucesso. Aqui estão suas informações de acesso:
            
            🏢 Condomínio: {tenant.nome}
            🌐 URL de Acesso: {url_acesso}
            📧 Email: {admin.email}
            
            📋 Próximos Passos:
            1. Faça login no sistema
            2. Configure suas preferências de email
            3. Cadastre os primeiros moradores
            4. Personalize as cores e logo do sistema
            
            🎯 Seu Plano: {tenant.plano_atual.nome}
            • Até {tenant.plano_atual.limite_moradores} moradores
            • {tenant.plano_atual.limite_usuarios} usuário(s)
            • {tenant.plano_atual.limite_anexos_mb}MB de armazenamento
            
            ⏰ Período de Avaliação: 30 dias grátis
            Vencimento: {tenant.data_vencimento.strftime('%d/%m/%Y')}
            
            🆘 Precisa de Ajuda?
            - Acesse nossa documentação
            - Entre em contato pelo suporte
            
            Obrigado por escolher nosso sistema!
            
            Equipe Sistema de Carteirinhas
            """
            
            # Enviar email
            EmailService.enviar_email(
                destinatario=admin.email,
                assunto=assunto,
                corpo=corpo_email
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar email de boas-vindas: {str(e)}")
    
    @staticmethod
    def gerar_subdominio_sugerido(nome_condominio):
        """Gera sugestões de subdomínio baseado no nome do condomínio"""
        from app.models import Tenant
        
        # Limpar nome
        nome_limpo = nome_condominio.lower()
        nome_limpo = ''.join(c for c in nome_limpo if c.isalnum() or c == ' ')
        nome_limpo = nome_limpo.replace(' ', '')
        
        # Sugestões
        sugestoes = []
        
        # Primeira sugestão: nome completo
        if len(nome_limpo) <= 20:
            sugestoes.append(nome_limpo)
        
        # Segunda sugestão: primeiras letras de cada palavra
        palavras = nome_condominio.split()
        if len(palavras) > 1:
            iniciais = ''.join(p[0].lower() for p in palavras if p)
            if len(iniciais) >= 3:
                sugestoes.append(iniciais)
        
        # Terceira sugestão: nome + números
        sugestoes.append(nome_limpo[:10] + '1')
        sugestoes.append(nome_limpo[:10] + '2')
        
        # Filtrar apenas disponíveis
        sugestoes_disponiveis = []
        for sugestao in sugestoes:
            if not Tenant.query.filter_by(subdominio=sugestao).first():
                sugestoes_disponiveis.append(sugestao)
        
        return sugestoes_disponiveis[:3]
    
    @staticmethod
    def validar_dados_cliente(dados):
        """Valida dados do cliente antes de criar conta"""
        erros = []
        
        # Validações obrigatórias
        campos_obrigatorios = ['nome', 'subdominio', 'email', 'nome_responsavel', 'senha', 'plano_id']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                erros.append(f"Campo '{campo}' é obrigatório")
        
        # Validar email
        if dados.get('email'):
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', dados['email']):
                erros.append("Email inválido")
        
        # Validar subdomínio
        if dados.get('subdominio'):
            subdominio = dados['subdominio']
            if len(subdominio) < 3:
                erros.append("Subdomínio deve ter pelo menos 3 caracteres")
            elif not subdominio.isalnum():
                erros.append("Subdomínio deve conter apenas letras e números")
            elif subdominio in ['www', 'api', 'admin', 'app', 'sistema']:
                erros.append("Subdomínio não permitido")
        
        # Validar senha
        if dados.get('senha'):
            senha = dados['senha']
            if len(senha) < 6:
                erros.append("Senha deve ter pelo menos 6 caracteres")
        
        # Validar CNPJ se fornecido
        if dados.get('cnpj'):
            cnpj = dados['cnpj']
            if not OnboardingService.validar_cnpj(cnpj):
                erros.append("CNPJ inválido")
        
        return erros
    
    @staticmethod
    def validar_cnpj(cnpj):
        """Validação básica de CNPJ"""
        if not cnpj:
            return True  # CNPJ é opcional
        
        # Remover caracteres especiais
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        # Verificar se tem 14 dígitos
        if len(cnpj) != 14:
            return False
        
        # Verificar se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Aqui você poderia implementar validação completa do CNPJ
        # Por simplicidade, vamos aceitar qualquer CNPJ com 14 dígitos
        return True
    
    @staticmethod
    def criar_dados_exemplo(tenant_id):
        """Cria dados de exemplo para demonstração"""
        from app.models import Morador
        
        moradores_exemplo = [
            {
                'nome_completo': 'João Silva',
                'bloco': 'A',
                'apartamento': '101',
                'email': 'joao@email.com',
                'celular': '(11) 99999-1111',
                'eh_titular': True,
                'tenant_id': tenant_id
            },
            {
                'nome_completo': 'Maria Santos',
                'bloco': 'B',
                'apartamento': '205',
                'email': 'maria@email.com',
                'celular': '(11) 99999-2222',
                'eh_titular': True,
                'tenant_id': tenant_id
            },
            {
                'nome_completo': 'Pedro Silva',
                'bloco': 'A',
                'apartamento': '101',
                'email': 'joao@email.com',
                'celular': '(11) 99999-3333',
                'eh_titular': False,
                'email_titular': 'joao@email.com',
                'tenant_id': tenant_id
            }
        ]
        
        for dados in moradores_exemplo:
            morador = Morador(**dados)
            db.session.add(morador)
        
        db.session.commit()
    
    @staticmethod
    def gerar_senha_temporaria():
        """Gera senha temporária para novos usuários"""
        caracteres = string.ascii_letters + string.digits
        return ''.join(secrets.choice(caracteres) for _ in range(8))
    
    @staticmethod
    def verificar_disponibilidade_subdominio(subdominio):
        """Verifica se subdomínio está disponível"""
        from app.models import Tenant
        
        # Verificar se já existe
        if Tenant.query.filter_by(subdominio=subdominio).first():
            return False, "Subdomínio já está em uso"
        
        # Verificar se é reservado
        reservados = ['www', 'api', 'admin', 'app', 'sistema', 'support', 'help']
        if subdominio.lower() in reservados:
            return False, "Subdomínio reservado"
        
        return True, "Subdomínio disponível" 