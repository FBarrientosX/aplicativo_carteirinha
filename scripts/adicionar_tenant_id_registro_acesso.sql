-- Script SQL para adicionar coluna tenant_id à tabela registro_acesso
-- Execute este script se a migração não funcionar

-- Verificar se a coluna já existe antes de adicionar
-- SQLite não suporta IF NOT EXISTS para colunas, então vamos usar uma abordagem diferente

-- Para SQLite, você precisa fazer uma nova tabela e copiar os dados
BEGIN TRANSACTION;

-- Criar tabela temporária com a nova estrutura
CREATE TABLE registro_acesso_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    morador_id INTEGER NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    data_hora DATETIME NOT NULL,
    metodo VARCHAR(20) NOT NULL,
    guardiao VARCHAR(100),
    observacoes TEXT,
    ip_origem VARCHAR(45),
    tenant_id INTEGER DEFAULT 1,
    FOREIGN KEY (morador_id) REFERENCES moradores(id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Copiar dados da tabela antiga para a nova
INSERT INTO registro_acesso_new (
    id, morador_id, tipo, data_hora, metodo, guardiao, observacoes, ip_origem, tenant_id
)
SELECT 
    id, morador_id, tipo, data_hora, metodo, guardiao, observacoes, ip_origem, 1 as tenant_id
FROM registro_acesso;

-- Remover tabela antiga
DROP TABLE registro_acesso;

-- Renomear tabela nova para o nome original
ALTER TABLE registro_acesso_new RENAME TO registro_acesso;

-- Criar índice
CREATE INDEX ix_registro_acesso_tenant_id ON registro_acesso(tenant_id);

COMMIT;

