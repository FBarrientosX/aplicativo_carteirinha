# Formulários específicos para administração
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from wtforms.widgets import TextArea
from app.models import Tenant, Plano
import re

class NovoCondominioForm(FlaskForm):
    """Formulário para cadastro de novo condomínio"""
    
    # Dados básicos do condomínio
    nome = StringField('Nome do Condomínio', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=200, message='Nome deve ter entre 3 e 200 caracteres')
    ])
    
    subdominio = StringField('Subdomínio', validators=[
        DataRequired(message='Subdomínio é obrigatório'),
        Length(min=3, max=50, message='Subdomínio deve ter entre 3 e 50 caracteres')
    ], render_kw={
        'placeholder': 'exemplo',
        'class': 'form-control',
        'data-toggle': 'tooltip',
        'title': 'Será usado como: exemplo.condotech.com.br'
    })
    
    # Dados do responsável
    nome_responsavel = StringField('Nome do Responsável', validators=[
        DataRequired(message='Nome do responsável é obrigatório'),
        Length(min=2, max=200, message='Nome deve ter entre 2 e 200 caracteres')
    ])
    
    email_responsavel = StringField('Email do Responsável', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=120, message='Email muito longo')
    ])
    
    telefone = StringField('Telefone', validators=[
        Optional(),
        Length(max=20, message='Telefone muito longo')
    ], render_kw={'placeholder': '(11) 99999-9999'})
    
    # Dados opcionais
    cnpj = StringField('CNPJ', validators=[
        Optional(),
        Length(min=14, max=18, message='CNPJ deve ter 14 dígitos')
    ], render_kw={'placeholder': '00.000.000/0001-00'})
    
    endereco = TextAreaField('Endereço Completo', validators=[
        Optional(),
        Length(max=500, message='Endereço muito longo')
    ], render_kw={'rows': 3, 'placeholder': 'Rua, número, bairro, cidade, CEP'})
    
    # Configurações iniciais
    plano_id = SelectField('Plano de Assinatura', 
                          coerce=int,
                          validators=[DataRequired(message='Selecione um plano')])
    
    senha_inicial = PasswordField('Senha Inicial do Administrador', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, max=50, message='Senha deve ter entre 6 e 50 caracteres')
    ])
    
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória')
    ])
    
    # Opções avançadas
    criar_dados_exemplo = BooleanField('Criar dados de exemplo', 
                                     default=True,
                                     description='Cria moradores de exemplo para demonstração')
    
    enviar_email_boas_vindas = BooleanField('Enviar email de boas-vindas',
                                          default=True,
                                          description='Envia instruções de acesso por email')
    
    # Campos ocultos para AJAX
    subdominio_disponivel = HiddenField()
    sugestoes_subdominio = HiddenField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carregar planos ativos
        self.plano_id.choices = [(0, 'Selecione um plano')]
        planos = Plano.query.filter_by(ativo=True, publico=True).order_by(Plano.ordem, Plano.nome).all()
        for plano in planos:
            descricao = f"{plano.nome} - R$ {plano.preco_mensal}/mês"
            if plano.limite_moradores:
                descricao += f" (até {plano.limite_moradores} moradores)"
            self.plano_id.choices.append((plano.id, descricao))
    
    def validate_subdominio(self, field):
        """Validação personalizada do subdomínio"""
        subdominio = field.data.lower().strip()
        
        # Verificar caracteres permitidos
        if not re.match(r'^[a-z0-9]+$', subdominio):
            raise ValidationError('Subdomínio deve conter apenas letras minúsculas e números')
        
        # Verificar se não é reservado
        reservados = ['www', 'api', 'admin', 'app', 'sistema', 'support', 'help', 'mail', 'ftp']
        if subdominio in reservados:
            raise ValidationError('Este subdomínio é reservado e não pode ser usado')
        
        # Verificar se já existe
        if Tenant.query.filter_by(subdominio=subdominio).first():
            raise ValidationError('Este subdomínio já está em uso')
    
    def validate_email_responsavel(self, field):
        """Validação do email do responsável"""
        # Verificar se email já está em uso por outro tenant
        from app.models import Usuario
        if Usuario.query.filter_by(email=field.data, tipo_usuario='admin').first():
            raise ValidationError('Este email já está cadastrado como administrador de outro condomínio')
    
    def validate_cnpj(self, field):
        """Validação do CNPJ"""
        if field.data:
            # Remover caracteres especiais
            cnpj = ''.join(filter(str.isdigit, field.data))
            
            # Verificar se tem 14 dígitos
            if len(cnpj) != 14:
                raise ValidationError('CNPJ deve ter 14 dígitos')
            
            # Verificar se todos os dígitos são iguais
            if cnpj == cnpj[0] * 14:
                raise ValidationError('CNPJ inválido')
            
            # Verificar se já existe
            if Tenant.query.filter_by(cnpj=field.data).first():
                raise ValidationError('Este CNPJ já está cadastrado')
    
    def validate_confirmar_senha(self, field):
        """Validação da confirmação de senha"""
        if field.data != self.senha_inicial.data:
            raise ValidationError('Senhas não coincidem')


class FiltroCondominiosForm(FlaskForm):
    """Formulário para filtrar condomínios na listagem"""
    
    busca = StringField('Buscar', validators=[Optional()], 
                       render_kw={'placeholder': 'Nome, subdomínio ou email...'})
    
    status = SelectField('Status', 
                        choices=[
                            ('', 'Todos os status'),
                            ('ativo', 'Ativos'),
                            ('suspenso', 'Suspensos'),
                            ('cancelado', 'Cancelados')
                        ],
                        default='')
    
    plano = SelectField('Plano',
                       choices=[('', 'Todos os planos')],
                       default='')
    
    vencimento = SelectField('Vencimento',
                           choices=[
                               ('', 'Todos'),
                               ('vencido', 'Vencidos'),
                               ('vence_30', 'Vence em 30 dias'),
                               ('vence_7', 'Vence em 7 dias')
                           ],
                           default='')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carregar planos para filtro
        planos = Plano.query.filter_by(ativo=True).order_by(Plano.nome).all()
        for plano in planos:
            self.plano.choices.append((str(plano.id), plano.nome))


class EditarCondominioForm(FlaskForm):
    """Formulário para editar condomínio existente"""
    
    nome = StringField('Nome do Condomínio', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=200, message='Nome deve ter entre 3 e 200 caracteres')
    ])
    
    email_responsavel = StringField('Email do Responsável', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=120, message='Email muito longo')
    ])
    
    telefone = StringField('Telefone', validators=[
        Optional(),
        Length(max=20, message='Telefone muito longo')
    ])
    
    cnpj = StringField('CNPJ', validators=[
        Optional(),
        Length(min=14, max=18, message='CNPJ deve ter 14 dígitos')
    ])
    
    endereco = TextAreaField('Endereço Completo', validators=[
        Optional(),
        Length(max=500, message='Endereço muito longo')
    ], render_kw={'rows': 3})
    
    plano_id = SelectField('Plano de Assinatura', 
                          coerce=int,
                          validators=[DataRequired(message='Selecione um plano')])
    
    status = SelectField('Status',
                        choices=[
                            ('ativo', 'Ativo'),
                            ('suspenso', 'Suspenso'),
                            ('cancelado', 'Cancelado')
                        ],
                        validators=[DataRequired()])
    
    dominio_personalizado = StringField('Domínio Personalizado', validators=[
        Optional(),
        Length(max=100, message='Domínio muito longo')
    ], render_kw={'placeholder': 'meucondominio.com.br'})
    
    def __init__(self, tenant=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        
        # Carregar planos ativos
        self.plano_id.choices = []
        planos = Plano.query.filter_by(ativo=True).order_by(Plano.ordem, Plano.nome).all()
        for plano in planos:
            descricao = f"{plano.nome} - R$ {plano.preco_mensal}/mês"
            self.plano_id.choices.append((plano.id, descricao))
    
    def validate_email_responsavel(self, field):
        """Validação do email do responsável"""
        if self.tenant and field.data != self.tenant.email_responsavel:
            from app.models import Usuario
            if Usuario.query.filter_by(email=field.data, tipo_usuario='admin').first():
                raise ValidationError('Este email já está cadastrado como administrador de outro condomínio')
    
    def validate_cnpj(self, field):
        """Validação do CNPJ"""
        if field.data:
            # Remover caracteres especiais
            cnpj = ''.join(filter(str.isdigit, field.data))
            
            if len(cnpj) != 14:
                raise ValidationError('CNPJ deve ter 14 dígitos')
            
            if cnpj == cnpj[0] * 14:
                raise ValidationError('CNPJ inválido')
            
            # Verificar se já existe (exceto o próprio)
            tenant_existente = Tenant.query.filter_by(cnpj=field.data).first()
            if tenant_existente and tenant_existente.id != self.tenant.id:
                raise ValidationError('Este CNPJ já está cadastrado')


class ConfigurarModulosForm(FlaskForm):
    """Formulário para configurar módulos do tenant"""
    
    modulo_piscina = BooleanField('Módulo Piscina', 
                                 default=True,
                                 description='Controle de acesso à piscina com carteirinhas')
    
    modulo_manutencao = BooleanField('Módulo Manutenção',
                                   default=False,
                                   description='Sistema de chamados de manutenção')
    
    modulo_salva_vidas = BooleanField('Módulo Salva-Vidas',
                                    default=False,
                                    description='Gestão da equipe de salva-vidas')
    
    modulo_financeiro = BooleanField('Módulo Financeiro',
                                   default=False,
                                   description='Controle financeiro e cobrança (em breve)')
    
    observacoes = TextAreaField('Observações', validators=[Optional()],
                               render_kw={'rows': 3, 'placeholder': 'Observações sobre a configuração dos módulos'})
