from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, DateField, SubmitField, SelectField, IntegerField, PasswordField, DecimalField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from datetime import datetime

def coerce_int_or_none(value):
    """Converte valor para int ou None se for string vazia"""
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class MoradorForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=200)])
    bloco = StringField('Bloco', validators=[DataRequired(), Length(min=1, max=10)])
    apartamento = StringField('Apartamento', validators=[DataRequired(), Length(min=1, max=10)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    celular = StringField('Celular', validators=[DataRequired(), Length(min=10, max=20)])
    
    eh_titular = BooleanField('É Titular?', default=True)
    email_titular = StringField('Email do Titular', validators=[Optional(), Email(), Length(max=120)])
    
    data_ultima_validacao = DateField('Data da Última Validação', validators=[Optional()])
    data_vencimento = DateField('Data de Vencimento', validators=[Optional()])
    
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=1000)])
    
    foto_carteirinha = FileField('Foto para Carteirinha', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], 
                   'Apenas imagens: jpg, jpeg, png, gif, bmp, webp')
    ])
    
    documentos = FileField('Documentos/Atestados Médicos', validators=[
        Optional(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'txt'], 
                   'Arquivos: pdf, jpg, jpeg, png, gif, doc, docx, txt')
    ])
    
    submit = SubmitField('Salvar')

class ValidarCarteirinhaForm(FlaskForm):
    meses_validade = SelectField('Validade (meses)', 
                                choices=[('6', '6 meses'), ('12', '12 meses')],
                                default='6',
                                validators=[DataRequired()])
    observacoes = TextAreaField('Observações da Validação', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Validar Carteirinha')

class FiltroMoradorForm(FlaskForm):
    bloco = SelectField('Bloco', choices=[('', 'Todos os blocos')], validators=[Optional()])
    status = SelectField('Status da Carteirinha', 
                        choices=[
                            ('', 'Todos'),
                            ('regular', 'Regular'),
                            ('a_vencer', 'A Vencer (30 dias)'),
                            ('vencida', 'Vencida'),
                            ('sem_carteirinha', 'Sem Carteirinha')
                        ],
                        validators=[Optional()])
    busca = StringField('Buscar por nome', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Filtrar')

class ConfiguracaoEmailForm(FlaskForm):
    """Formulário para configuração de email"""
    mail_server = StringField('Servidor SMTP', validators=[DataRequired()], 
                             render_kw={'placeholder': 'smtp.gmail.com'})
    mail_port = IntegerField('Porta', validators=[DataRequired()], default=587)
    mail_use_tls = BooleanField('Usar TLS', default=True)
    mail_username = StringField('Email/Usuário', validators=[DataRequired(), Email()],
                               render_kw={'placeholder': 'seu_email@gmail.com'})
    mail_password = PasswordField('Senha', validators=[DataRequired()],
                                 render_kw={'placeholder': 'Senha de app (Gmail/Yahoo)'})
    mail_default_sender = StringField('Email Remetente', validators=[Optional(), Email()],
                                     render_kw={'placeholder': 'Deixe vazio para usar o mesmo do usuário'})
    submit = SubmitField('Salvar Configurações')

class ConfiguracaoCondominioForm(FlaskForm):
    """Formulário para configuração do condomínio"""
    nome = StringField('Nome do Condomínio', validators=[DataRequired()],
                      render_kw={'placeholder': 'Ex: Residencial Águas Claras'})
    cnpj = StringField('CNPJ', 
                      render_kw={'placeholder': '00.000.000/0000-00'})
    endereco = TextAreaField('Endereço Completo',
                            render_kw={'placeholder': 'Rua, número, bairro, cidade, CEP'})
    telefone = StringField('Telefone', 
                          render_kw={'placeholder': '(11) 3333-4444'})
    email_administracao = StringField('Email da Administração', validators=[Email()],
                                     render_kw={'placeholder': 'admin@condominio.com'})
    whatsapp = StringField('WhatsApp', 
                          render_kw={'placeholder': '(11) 99999-9999'})
    horario_funcionamento = StringField('Horário de Funcionamento',
                                       render_kw={'placeholder': 'Segunda a Sexta, 8h às 18h'})
    
    # Configurações específicas
    dias_aviso_vencimento = IntegerField('Dias de Aviso (Vencimento)', 
                                        validators=[DataRequired()], default=30)
    meses_validade_padrao = IntegerField('Meses de Validade Padrão', 
                                        validators=[DataRequired()], default=12)
    permitir_dependentes = BooleanField('Permitir Dependentes', default=True)
    
    # Personalização visual
    cor_primaria = StringField('Cor Primária', default='#007bff',
                              render_kw={'type': 'color'})
    cor_secundaria = StringField('Cor Secundária', default='#6c757d',
                                render_kw={'type': 'color'})
    
    submit = SubmitField('Salvar Configurações')

class ConfiguracaoGeralForm(FlaskForm):
    """Formulário para configurações gerais do sistema"""
    nome_sistema = StringField('Nome do Sistema', validators=[DataRequired()],
                              default='Sistema de Carteirinhas')
    versao = StringField('Versão', default='1.0.0', 
                        render_kw={'readonly': True})
    
    # Configurações de segurança
    sessao_timeout = IntegerField('Timeout da Sessão (minutos)', 
                                 validators=[DataRequired()], default=120)
    max_tentativas_login = IntegerField('Máximo de Tentativas de Login', 
                                       validators=[DataRequired()], default=5)
    
    # Configurações de backup
    backup_automatico = BooleanField('Backup Automático', default=True)
    dias_backup = IntegerField('Intervalo de Backup (dias)', default=7)
    
    # Configurações de notificações
    notificacoes_automaticas = BooleanField('Notificações Automáticas', default=True)
    horario_notificacoes = StringField('Horário das Notificações', default='09:00',
                                      render_kw={'type': 'time'})
    
    submit = SubmitField('Salvar Configurações')

class NotificacaoManualForm(FlaskForm):
    """Formulário para envio manual de notificações"""
    tipo_notificacao = SelectField('Tipo de Notificação', 
                                  choices=[
                                      ('30_dias', 'Aviso de Vencimento (30 dias)'),
                                      ('vencimento', 'Carteirinha Vencida'),
                                      ('personalizada', 'Mensagem Personalizada')
                                  ],
                                  validators=[DataRequired()])
    assunto_personalizado = StringField('Assunto (se personalizada)', validators=[Optional()])
    mensagem_personalizada = TextAreaField('Mensagem (se personalizada)', validators=[Optional()])
    moradores_selecionados = StringField('IDs dos Moradores', validators=[Optional()])
    submit = SubmitField('Enviar Notificações')

class AjusteVencimentoForm(FlaskForm):
    """Formulário para ajuste rápido de vencimento"""
    nova_data_vencimento = DateField('Nova Data de Vencimento', validators=[DataRequired()])
    motivo_ajuste = TextAreaField('Motivo do Ajuste', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Ajustar Vencimento')

class SalvaVidasForm(FlaskForm):
    """Formulário para cadastro e edição de salva-vidas"""
    # Dados pessoais
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=200)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)],
                     render_kw={'placeholder': '000.000.000-00'})
    rg = StringField('RG', validators=[Optional(), Length(max=20)],
                    render_kw={'placeholder': '00.000.000-0'})
    data_nascimento = DateField('Data de Nascimento', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)],
                          render_kw={'placeholder': '(11) 99999-9999'})
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    endereco = TextAreaField('Endereço', validators=[Optional(), Length(max=500)])
    
    # Dados profissionais
    data_contratacao = DateField('Data de Contratação', validators=[DataRequired()])
    data_demissao = DateField('Data de Demissão', validators=[Optional()])
    status = SelectField('Status', 
                        choices=[
                            ('ativo', 'Ativo'),
                            ('inativo', 'Inativo'),
                            ('demitido', 'Demitido'),
                            ('férias', 'Férias'),
                            ('licença', 'Licença Médica')
                        ],
                        default='ativo',
                        validators=[DataRequired()])
    salario = DecimalField('Salário (R$)', validators=[Optional(), NumberRange(min=0)],
                          render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    # Certificações
    certificacao_salvamento = BooleanField('Certificação em Salvamento Aquático')
    certificacao_primeiros_socorros = BooleanField('Certificação em Primeiros Socorros')
    data_vencimento_certificacao = DateField('Vencimento das Certificações', validators=[Optional()])
    outras_qualificacoes = TextAreaField('Outras Qualificações', validators=[Optional(), Length(max=500)])
    
    # Horários
    horario_trabalho = TextAreaField('Horário de Trabalho', validators=[Optional(), Length(max=500)],
                                    render_kw={'placeholder': 'Ex: Segunda a Sexta: 8h às 16h\nSábado: 8h às 12h'})
    
    # Observações
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=1000)])
    
    # Upload de foto
    foto = FileField('Foto do Salva-vidas', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens: jpg, jpeg, png, gif')
    ])
    
    submit = SubmitField('Salvar')

class FiltroSalvaVidasForm(FlaskForm):
    """Formulário para filtrar salva-vidas"""
    status = SelectField('Status', 
                        choices=[
                            ('', 'Todos'),
                            ('ativo', 'Ativo'),
                            ('inativo', 'Inativo'),
                            ('demitido', 'Demitido'),
                            ('férias', 'Férias'),
                            ('licença', 'Licença Médica')
                        ],
                        validators=[Optional()])
    certificacao = SelectField('Certificação',
                              choices=[
                                  ('', 'Todas'),
                                  ('salvamento', 'Salvamento Aquático'),
                                  ('primeiros_socorros', 'Primeiros Socorros'),
                                  ('ambas', 'Ambas as Certificações')
                              ],
                              validators=[Optional()])
    busca = StringField('Buscar por nome', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Filtrar')

class RegistroAcessoForm(FlaskForm):
    """Formulário para registrar entrada/saída manual"""
    morador_id = SelectField('Morador', coerce=int, validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada'), ('saida', 'Saída')], validators=[DataRequired()])
    guardiao = StringField('Nome do Guardião', validators=[DataRequired(), Length(max=100)])
    observacoes = TextAreaField('Observações', validators=[Length(max=500)])
    submit = SubmitField('Registrar Acesso')
    
    def __init__(self, *args, **kwargs):
        super(RegistroAcessoForm, self).__init__(*args, **kwargs)
        # Carregar moradores ativos do tenant atual
        from app.models import Morador
        from flask import g
        
        tenant_id = getattr(g, 'tenant_id', 1)
        moradores_query = Morador.query.filter(
            Morador.carteirinha_ativa == True,
            Morador.tenant_id == tenant_id
        ).order_by(Morador.nome_completo)
        
        self.morador_id.choices = [(0, 'Selecione um morador')] + [
            (m.id, f"{m.nome_completo} - {m.bloco}-{m.apartamento}")
            for m in moradores_query.all()
        ]

class BuscaMoradorForm(FlaskForm):
    """Formulário para buscar morador por QR Code ou manualmente"""
    codigo_qr = StringField('Código QR ou ID do Morador')
    busca_nome = StringField('Buscar por Nome')
    submit_qr = SubmitField('Processar QR Code')
    submit_busca = SubmitField('Buscar Morador')

class FiltroAcessoForm(FlaskForm):
    """Formulário para filtrar registros de acesso"""
    morador_id = SelectField('Morador', coerce=int)
    data_inicio = DateField('Data Início')
    data_fim = DateField('Data Fim')
    tipo = SelectField('Tipo', choices=[('', 'Todos'), ('entrada', 'Entradas'), ('saida', 'Saídas')])
    submit = SubmitField('Filtrar')

class LoginForm(FlaskForm):
    """Formulário de login"""
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class CadastroUsuarioForm(FlaskForm):
    """Formulário para cadastro de usuário"""
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=200)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar Senha', validators=[DataRequired()])
    tipo_usuario = SelectField('Tipo de Usuário', 
                              choices=[('admin', 'Administrador'), ('salva_vidas', 'Salva-vidas')],
                              validators=[DataRequired()])
    salva_vidas_id = SelectField('Salva-vidas Associado', coerce=coerce_int_or_none, validators=[Optional()])
    submit = SubmitField('Cadastrar')
    
    def validate_password2(self, password2):
        if self.password.data != password2.data:
            raise ValidationError('As senhas devem ser iguais.') 

# Forms para o módulo de Manutenção & Chamados
class ChamadoManutencaoForm(FlaskForm):
    """Formulário para criar/editar chamados de manutenção"""
    titulo = StringField('Título', validators=[DataRequired(), Length(max=200)])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    local = StringField('Local', validators=[DataRequired(), Length(max=200)])
    categoria_id = SelectField('Categoria', validators=[DataRequired()], coerce=int)
    prioridade = SelectField('Prioridade', 
                           choices=[('baixa', 'Baixa'), ('media', 'Média'), 
                                   ('alta', 'Alta'), ('urgente', 'Urgente')],
                           validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[('aberto', 'Aberto'), ('em_andamento', 'Em Andamento'),
                                ('aguardando', 'Aguardando'), ('concluido', 'Concluído'),
                                ('cancelado', 'Cancelado')])
    responsavel_id = SelectField('Responsável', coerce=int)

class FiltrosChamadosForm(FlaskForm):
    """Formulário para filtros de chamados"""
    status = SelectField('Status', choices=[('', 'Todos')])
    categoria = SelectField('Categoria', choices=[('', 'Todas')])
    prioridade = SelectField('Prioridade', choices=[('', 'Todas')])
    busca = StringField('Buscar') 