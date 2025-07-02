from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, DateField, SubmitField, SelectField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional
from datetime import datetime

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
    
    anexo = FileField('Anexar Arquivo', validators=[
        Optional(),
        FileAllowed(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'], 
                   'Apenas arquivos: txt, pdf, png, jpg, jpeg, gif, doc, docx')
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