"""
Formulários do módulo Piscina
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional


class RegistroAcessoPiscinaForm(FlaskForm):
    morador_id = HiddenField('Morador ID', validators=[DataRequired()])
    morador_nome = StringField('Morador', render_kw={'readonly': True})
    tipo = SelectField('Tipo de Registro',
                      choices=[('entrada', 'Entrada'), ('saida', 'Saída')],
                      validators=[DataRequired()],
                      default='entrada')
    metodo = SelectField('Método',
                        choices=[('manual', 'Registro Manual'), ('qr_code', 'QR Code')],
                        default='manual')
    observacoes = TextAreaField('Observações', validators=[Optional(),])
    submit = SubmitField('Confirmar Registro')


class OcorrenciaPiscinaForm(FlaskForm):
    morador_id = HiddenField('Morador ID', validators=[Optional()])
    tipo = SelectField('Tipo',
                      choices=[
                          ('acidente', 'Acidente'),
                          ('incidente', 'Incidente'),
                          ('advertencia', 'Advertência'),
                          ('outro', 'Outro')
                      ],
                      validators=[DataRequired()])
    severidade = SelectField('Severidade',
                            choices=[
                                ('baixa', 'Baixa'),
                                ('media', 'Média'),
                                ('alta', 'Alta'),
                                ('critica', 'Crítica')
                            ],
                            validators=[DataRequired()],
                            default='baixa')
    titulo = StringField('Título', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Registrar Ocorrência')
"""
Formulários do Módulo Piscina
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class RegistroAcessoForm(FlaskForm):
    """Formulário para registro de acesso"""
    morador_id = HiddenField('Morador ID', validators=[DataRequired()])
    tipo = SelectField('Tipo', 
                      choices=[('entrada', 'Entrada'), ('saida', 'Saída')],
                      validators=[DataRequired()])
    metodo = SelectField('Método',
                        choices=[('qr_code', 'QR Code'), ('manual', 'Manual'), ('barcode', 'Código de Barras')],
                        default='manual',
                        validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Confirmar Registro')


class OcorrenciaPiscinaForm(FlaskForm):
    """Formulário para registro de ocorrência"""
    tipo = SelectField('Tipo de Ocorrência',
                     choices=[
                         ('acidente', 'Acidente'),
                         ('incidente', 'Incidente'),
                         ('advertencia', 'Advertência'),
                         ('outro', 'Outro')
                     ],
                     validators=[DataRequired()])
    severidade = SelectField('Severidade',
                           choices=[
                               ('baixa', 'Baixa'),
                               ('media', 'Média'),
                               ('alta', 'Alta'),
                               ('critica', 'Crítica')
                           ],
                           validators=[DataRequired()])
    morador_id = SelectField('Morador Envolvido (Opcional)',
                           choices=[('', 'Nenhum')],
                           validators=[Optional()],
                           coerce=lambda x: int(x) if x else None)
    titulo = StringField('Título', validators=[DataRequired(), Length(max=200)])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    fotos = FileField('Fotos (Opcional)',
                     validators=[
                         Optional(),
                         FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens')
                     ])
    submit = SubmitField('Salvar Ocorrência')

