from app import db
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy

class CategoriaFinanceira(db.Model):
    """Categorias para receitas e despesas"""
    __tablename__ = 'categorias_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.Enum('receita', 'despesa', name='tipo_categoria'), nullable=False)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    cor = db.Column(db.String(7), default='#007bff')  # Cor em hex para interface
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    receitas = db.relationship('Receita', backref='categoria', lazy='dynamic')
    despesas = db.relationship('Despesa', backref='categoria', lazy='dynamic')
    
    def __repr__(self):
        return f'<CategoriaFinanceira {self.nome}>'

class ContaBancaria(db.Model):
    """Contas bancárias do condomínio"""
    __tablename__ = 'contas_bancarias'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    banco = db.Column(db.String(100), nullable=False)
    agencia = db.Column(db.String(20), nullable=False)
    conta = db.Column(db.String(20), nullable=False)
    tipo_conta = db.Column(db.Enum('corrente', 'poupanca', 'investimento', name='tipo_conta_bancaria'), nullable=False)
    saldo_inicial = db.Column(db.Numeric(15, 2), default=0)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoFinanceira', backref='conta_bancaria', lazy='dynamic')
    
    def __repr__(self):
        return f'<ContaBancaria {self.nome} - {self.banco}>'
    
    @property
    def saldo_atual(self):
        """Calcula o saldo atual da conta"""
        movimentacoes = self.movimentacoes.filter_by(ativo=True).all()
        saldo = self.saldo_inicial
        for mov in movimentacoes:
            if mov.tipo == 'receita':
                saldo += mov.valor
            else:
                saldo -= mov.valor
        return saldo

class Receita(db.Model):
    """Receitas do condomínio"""
    __tablename__ = 'receitas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_financeiras.id'), nullable=False)
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey('contas_bancarias.id'), nullable=True)
    
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    data_recebimento = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('pendente', 'recebido', 'atrasado', 'cancelado', name='status_receita'), default='pendente')
    
    # Dados do pagador
    pagador_nome = db.Column(db.String(200))
    pagador_documento = db.Column(db.String(20))
    pagador_apartamento = db.Column(db.String(20))
    
    # Dados adicionais
    observacoes = db.Column(db.Text)
    comprovante = db.Column(db.String(255))  # Caminho do arquivo
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoFinanceira', backref='receita', lazy='dynamic')
    
    def __repr__(self):
        return f'<Receita {self.descricao} - R$ {self.valor}>'

class Despesa(db.Model):
    """Despesas do condomínio"""
    __tablename__ = 'despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_financeiras.id'), nullable=False)
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey('contas_bancarias.id'), nullable=True)
    
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    data_pagamento = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('pendente', 'pago', 'atrasado', 'cancelado', name='status_despesa'), default='pendente')
    
    # Dados do fornecedor
    fornecedor_nome = db.Column(db.String(200))
    fornecedor_documento = db.Column(db.String(20))
    
    # Dados adicionais
    observacoes = db.Column(db.Text)
    comprovante = db.Column(db.String(255))  # Caminho do arquivo
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoFinanceira', backref='despesa', lazy='dynamic')
    
    def __repr__(self):
        return f'<Despesa {self.descricao} - R$ {self.valor}>'

class MovimentacaoFinanceira(db.Model):
    """Movimentações financeiras (receitas e despesas)"""
    __tablename__ = 'movimentacoes_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey('contas_bancarias.id'), nullable=False)
    receita_id = db.Column(db.Integer, db.ForeignKey('receitas.id'), nullable=True)
    despesa_id = db.Column(db.Integer, db.ForeignKey('despesas.id'), nullable=True)
    
    tipo = db.Column(db.Enum('receita', 'despesa', name='tipo_movimentacao'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    data_movimentacao = db.Column(db.Date, nullable=False)
    saldo_anterior = db.Column(db.Numeric(15, 2), nullable=False)
    saldo_posterior = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Dados adicionais
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MovimentacaoFinanceira {self.tipo} - R$ {self.valor}>'

class CobrancaFinanceira(db.Model):
    """Cobranças de condomínio por apartamento"""
    __tablename__ = 'cobrancas_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    
    # Dados do apartamento (redundantes para facilitar consultas)
    bloco = db.Column(db.String(10), nullable=False)
    apartamento = db.Column(db.String(10), nullable=False)
    
    mes_referencia = db.Column(db.Date, nullable=False)  # Mês de referência da cobrança
    valor_condominio = db.Column(db.Numeric(15, 2), nullable=False)
    valor_extra = db.Column(db.Numeric(15, 2), default=0)  # Taxas extras, multas, etc.
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)
    
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('pendente', 'pago', 'atrasado', 'cancelado', name='status_cobranca'), default='pendente')
    
    # Dados de pagamento
    forma_pagamento = db.Column(db.Enum('dinheiro', 'pix', 'transferencia', 'boleto', 'cartao', name='forma_pagamento'), nullable=True)
    comprovante = db.Column(db.String(255))  # Caminho do arquivo
    
    # Dados adicionais
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    morador = db.relationship('Morador', backref='cobrancas')
    
    def __repr__(self):
        return f'<Cobranca {self.bloco}/{self.apartamento} - {self.mes_referencia}>'
    
    @property
    def dias_atraso(self):
        """Calcula dias de atraso se a cobrança estiver atrasada"""
        if self.status == 'atrasado' and self.data_vencimento < date.today():
            return (date.today() - self.data_vencimento).days
        return 0
    
    @property
    def apartamento_completo(self):
        """Retorna bloco/apartamento formatado"""
        return f"{self.bloco}/{self.apartamento}"

class CobrancaLote(db.Model):
    """Lote de cobranças geradas em massa"""
    __tablename__ = 'cobrancas_lote'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Dados do lote
    mes_referencia = db.Column(db.Date, nullable=False)
    valor_condominio = db.Column(db.Numeric(15, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    
    # Estatísticas do lote
    total_apartamentos = db.Column(db.Integer, default=0)
    total_gerado = db.Column(db.Integer, default=0)
    total_erros = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='processando')  # processando, concluido, erro
    
    # Controle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<CobrancaLote {self.mes_referencia} - {self.total_gerado} cobranças>'

class ConfiguracaoFinanceira(db.Model):
    """Configurações do módulo financeiro"""
    __tablename__ = 'configuracoes_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, unique=True)
    
    # Configurações de cobrança
    valor_condominio_padrao = db.Column(db.Numeric(15, 2), default=0)
    dia_vencimento = db.Column(db.Integer, default=10)  # Dia do mês para vencimento
    multa_atraso = db.Column(db.Numeric(5, 2), default=2.00)  # Percentual de multa
    juros_dia = db.Column(db.Numeric(5, 2), default=0.10)  # Percentual de juros por dia
    
    # Configurações de relatórios
    relatorio_mes_atual = db.Column(db.Boolean, default=True)
    incluir_projecoes = db.Column(db.Boolean, default=True)
    
    # Configurações de backup
    backup_automatico = db.Column(db.Boolean, default=False)
    frequencia_backup = db.Column(db.Enum('diario', 'semanal', 'mensal', name='frequencia_backup'), default='semanal')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConfiguracaoFinanceira Tenant {self.tenant_id}>'

class TaxaCondominio(db.Model):
    """Taxas do condomínio"""
    __tablename__ = 'taxas_condominio'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    # Informações básicas
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(20), nullable=False)  # 'percentual' ou 'valor_fixo'
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(20), default='adicional')  # 'padrao', 'adicional', 'multa', 'reserva'
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Controle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    def __repr__(self):
        return f'<TaxaCondominio {self.nome} ({self.tipo})>'

    @property
    def valor_formatado(self):
        """Retorna o valor formatado com a unidade correta"""
        if self.tipo == 'percentual':
            return f"{self.valor}%"
        else:
            return f"R$ {self.valor:.2f}"

class HistoricoTaxa(db.Model):
    """Histórico de alterações das taxas"""
    __tablename__ = 'historico_taxas'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    taxa_id = db.Column(db.Integer, db.ForeignKey('taxas_condominio.id'), nullable=False)
    
    # Alteração
    campo_alterado = db.Column(db.String(50), nullable=False)
    valor_anterior = db.Column(db.String(100))
    valor_novo = db.Column(db.String(100))
    
    # Controle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer)

    def __repr__(self):
        return f'<HistoricoTaxa {self.taxa_id} - {self.campo_alterado}>'

# Métodos auxiliares para consultas financeiras
class FinanceiroService:
    """Serviços auxiliares para operações financeiras"""
    
    @staticmethod
    def calcular_saldo_periodo(tenant_id, data_inicio, data_fim, conta_id=None):
        """Calcula o saldo em um período específico"""
        query = MovimentacaoFinanceira.query.filter_by(tenant_id=tenant_id, ativo=True)
        
        if conta_id:
            query = query.filter_by(conta_bancaria_id=conta_id)
        
        query = query.filter(
            MovimentacaoFinanceira.data_movimentacao.between(data_inicio, data_fim)
        )
        
        movimentacoes = query.all()
        
        receitas = sum([m.valor for m in movimentacoes if m.tipo == 'receita'])
        despesas = sum([m.valor for m in movimentacoes if m.tipo == 'despesa'])
        
        return {
            'receitas': receitas,
            'despesas': despesas,
            'saldo': receitas - despesas
        }
    
    @staticmethod
    def gerar_fluxo_caixa(tenant_id, data_inicio, data_fim):
        """Gera o fluxo de caixa para um período"""
        # Implementar lógica de fluxo de caixa
        pass
    
    @staticmethod
    def calcular_inadimplencia(tenant_id, mes_referencia):
        """Calcula a inadimplência para um mês"""
        cobrancas = CobrancaFinanceira.query.filter_by(
            tenant_id=tenant_id,
            mes_referencia=mes_referencia,
            ativo=True
        ).all()
        
        total_cobrancas = len(cobrancas)
        cobrancas_pagas = len([c for c in cobrancas if c.status == 'pago'])
        cobrancas_atrasadas = len([c for c in cobrancas if c.status == 'atrasado'])
        
        if total_cobrancas > 0:
            percentual_pago = (cobrancas_pagas / total_cobrancas) * 100
            percentual_atrasado = (cobrancas_atrasadas / total_cobrancas) * 100
        else:
            percentual_pago = 0
            percentual_atrasado = 0
        
        return {
            'total_cobrancas': total_cobrancas,
            'cobrancas_pagas': cobrancas_pagas,
            'cobrancas_atrasadas': cobrancas_atrasadas,
            'percentual_pago': percentual_pago,
            'percentual_atrasado': percentual_atrasado
        }
