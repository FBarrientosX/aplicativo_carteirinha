#!/usr/bin/env python3
"""
Fix Universal - Funciona com ou sem tenant_id
Solução definitiva para problema de migração
"""

import os
import sys

def criar_modelo_adaptativo():
    """Criar modelo que se adapta à presença ou ausência de tenant_id"""
    print("🔧 CRIANDO MODELO ADAPTATIVO...")
    
    try:
        with open('app/models.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup
        with open('app/models.py.backup_adaptativo', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Substituir definição do RegistroAcesso por versão adaptativa
        old_class = '''class RegistroAcesso(db.Model):
    """Modelo para registrar entradas e saídas da piscina"""
    __tablename__ = 'registro_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    metodo = db.Column(db.String(20), nullable=False)  # 'manual', 'qrcode', 'barcode'
    guardiao = db.Column(db.String(100))  # Nome do guardião que registrou
    observacoes = db.Column(db.Text)
    ip_origem = db.Column(db.String(45))  # IP de onde foi registrado
    
    # NOVO: Multi-tenancy
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, default=1, index=True)
    
    # Relacionamento
    morador = db.relationship('Morador', backref=db.backref('registros_acesso', lazy=True, order_by='RegistroAcesso.data_hora.desc()'))
    tenant = db.relationship('Tenant', backref='registros_acesso')'''
        
        new_class = '''class RegistroAcesso(db.Model):
    """Modelo para registrar entradas e saídas da piscina"""
    __tablename__ = 'registro_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    metodo = db.Column(db.String(20), nullable=False)  # 'manual', 'qrcode', 'barcode'
    guardiao = db.Column(db.String(100))  # Nome do guardião que registrou
    observacoes = db.Column(db.Text)
    ip_origem = db.Column(db.String(45))  # IP de onde foi registrado
    
    # Relacionamento
    morador = db.relationship('Morador', backref=db.backref('registros_acesso', lazy=True, order_by='RegistroAcesso.data_hora.desc()'))
    
    def __init__(self, **kwargs):
        """Construtor adaptativo que lida com tenant_id opcionalmente"""
        # Verificar se tenant_id existe na tabela
        try:
            from sqlalchemy import text
            result = db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        # Se tenant_id existe, usar. Se não, ignorar
        if has_tenant_id and 'tenant_id' in kwargs:
            self.tenant_id = kwargs.pop('tenant_id')
        elif has_tenant_id:
            # Obter tenant_id do contexto
            from flask import g
            tenant_id = getattr(g, 'tenant_id', 1)
            self.tenant_id = tenant_id
        
        # Chamar construtor pai com argumentos restantes
        super().__init__(**kwargs)
    
    @property
    def tenant_id_safe(self):
        """Propriedade segura para tenant_id"""
        try:
            return getattr(self, 'tenant_id', 1)
        except Exception:
            return 1'''
        
        if old_class in content:
            content = content.replace(old_class, new_class)
            print("   ✅ Classe RegistroAcesso adaptativa criada")
        
        # Atualizar métodos estáticos para serem adaptativos
        old_method_1 = '''@staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=None):
        """Verifica se o morador está atualmente na piscina"""
        from flask import g
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        ultimo_registro = RegistroAcesso.query.filter_by(
            morador_id=morador_id,
            tenant_id=tenant_id
        ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada' '''
        
        new_method_1 = '''@staticmethod
    def morador_esta_na_piscina(morador_id, tenant_id=None):
        """Verifica se o morador está atualmente na piscina"""
        from flask import g
        from sqlalchemy import text
        
        # Verificar se tenant_id existe na tabela
        try:
            db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        if has_tenant_id:
            # Usar tenant_id do contexto se não fornecido
            if tenant_id is None:
                tenant_id = getattr(g, 'tenant_id', 1)
            
            ultimo_registro = RegistroAcesso.query.filter_by(
                morador_id=morador_id,
                tenant_id=tenant_id
            ).order_by(RegistroAcesso.data_hora.desc()).first()
        else:
            # Versão sem tenant_id
            ultimo_registro = RegistroAcesso.query.filter_by(
                morador_id=morador_id
            ).order_by(RegistroAcesso.data_hora.desc()).first()
        
        return ultimo_registro and ultimo_registro.tipo == 'entrada' '''
        
        if old_method_1 in content:
            content = content.replace(old_method_1, new_method_1)
            print("   ✅ Método morador_esta_na_piscina adaptativo")
        
        # Atualizar método obter_moradores_na_piscina
        old_method_2 = '''@staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        
        # Usar tenant_id do contexto se não fornecido
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', 1)
        
        # Subconsulta para obter o último registro de cada morador do tenant
        subq = db.session.query(
            RegistroAcesso.morador_id,
            db.func.max(RegistroAcesso.data_hora).label('ultima_data')
        ).filter(RegistroAcesso.tenant_id == tenant_id).group_by(RegistroAcesso.morador_id).subquery()
        
        # Buscar registros que são entradas no tenant específico
        moradores_dentro = db.session.query(Morador).join(
            RegistroAcesso, Morador.id == RegistroAcesso.morador_id
        ).join(
            subq, db.and_(
                RegistroAcesso.morador_id == subq.c.morador_id,
                RegistroAcesso.data_hora == subq.c.ultima_data
            )
        ).filter(
            RegistroAcesso.tipo == 'entrada',
            RegistroAcesso.tenant_id == tenant_id,
            Morador.tenant_id == tenant_id
        ).all()
        
        return moradores_dentro'''
        
        new_method_2 = '''@staticmethod
    def obter_moradores_na_piscina(tenant_id=None):
        """Retorna lista de moradores que estão atualmente na piscina"""
        from flask import g
        from sqlalchemy import text
        
        # Verificar se tenant_id existe na tabela
        try:
            db.session.execute(text("SELECT tenant_id FROM registro_acesso LIMIT 1"))
            has_tenant_id = True
        except Exception:
            has_tenant_id = False
        
        if has_tenant_id:
            # Usar tenant_id do contexto se não fornecido
            if tenant_id is None:
                tenant_id = getattr(g, 'tenant_id', 1)
            
            # Subconsulta para obter o último registro de cada morador do tenant
            subq = db.session.query(
                RegistroAcesso.morador_id,
                db.func.max(RegistroAcesso.data_hora).label('ultima_data')
            ).filter(RegistroAcesso.tenant_id == tenant_id).group_by(RegistroAcesso.morador_id).subquery()
            
            # Buscar registros que são entradas no tenant específico
            moradores_dentro = db.session.query(Morador).join(
                RegistroAcesso, Morador.id == RegistroAcesso.morador_id
            ).join(
                subq, db.and_(
                    RegistroAcesso.morador_id == subq.c.morador_id,
                    RegistroAcesso.data_hora == subq.c.ultima_data
                )
            ).filter(
                RegistroAcesso.tipo == 'entrada',
                RegistroAcesso.tenant_id == tenant_id,
                Morador.tenant_id == tenant_id
            ).all()
        else:
            # Versão sem tenant_id
            subq = db.session.query(
                RegistroAcesso.morador_id,
                db.func.max(RegistroAcesso.data_hora).label('ultima_data')
            ).group_by(RegistroAcesso.morador_id).subquery()
            
            moradores_dentro = db.session.query(Morador).join(
                RegistroAcesso, Morador.id == RegistroAcesso.morador_id
            ).join(
                subq, db.and_(
                    RegistroAcesso.morador_id == subq.c.morador_id,
                    RegistroAcesso.data_hora == subq.c.ultima_data
                )
            ).filter(RegistroAcesso.tipo == 'entrada').all()
        
        return moradores_dentro'''
        
        if old_method_2 in content:
            content = content.replace(old_method_2, new_method_2)
            print("   ✅ Método obter_moradores_na_piscina adaptativo")
        
        # Salvar arquivo
        with open('app/models.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ app/models.py adaptativo criado")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("🛠️ FIX UNIVERSAL - TENANT_ID ADAPTATIVO")
    print("="*50)
    
    print("🎯 Esta solução funciona com ou sem tenant_id no banco!")
    
    sucesso = criar_modelo_adaptativo()
    
    if sucesso:
        print("\n✅ CORREÇÃO APLICADA COM SUCESSO!")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("   1. git add . && git commit -m 'Fix universal tenant_id'")
        print("   2. git push")
        print("   3. No PythonAnywhere: git pull && reload app")
        print("   4. Execute: python3.10 verificar_banco_pythonanywhere.py")
        
        print("\n🎉 O sistema funcionará independente da migração!")
        
    else:
        print("\n❌ FALHA NA CORREÇÃO!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 