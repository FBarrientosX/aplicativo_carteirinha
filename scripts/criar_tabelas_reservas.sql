-- Script SQL para criar tabelas de reservas de espaços
-- Execute este script no banco de dados se a migration não funcionar

-- Criar tabela espacos_comuns
CREATE TABLE IF NOT EXISTS espacos_comuns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    capacidade_maxima INTEGER,
    area_metros NUMERIC(10, 2),
    tempo_antecipacao_horas INTEGER DEFAULT 24,
    tempo_maximo_horas INTEGER DEFAULT 4,
    valor_taxa NUMERIC(10, 2) DEFAULT 0,
    requer_aprovacao BOOLEAN DEFAULT 0,
    horario_inicio TIME,
    horario_fim TIME,
    dias_semana_disponiveis VARCHAR(20) DEFAULT '0123456',
    ativo BOOLEAN DEFAULT 1,
    fotos TEXT,  -- JSON armazenado como TEXT no SQLite
    equipamentos TEXT,
    data_criacao DATETIME,
    data_atualizacao DATETIME,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Criar tabela reservas_espacos
CREATE TABLE IF NOT EXISTS reservas_espacos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero VARCHAR(20) NOT NULL UNIQUE,
    tenant_id INTEGER NOT NULL,
    espaco_id INTEGER NOT NULL,
    morador_id INTEGER NOT NULL,
    data_reserva DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    quantidade_pessoas INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pendente',
    aprovado_por INTEGER,
    data_aprovacao DATETIME,
    motivo_recusa TEXT,
    finalidade VARCHAR(200),
    observacoes TEXT,
    taxa_paga BOOLEAN DEFAULT 0,
    valor_pago NUMERIC(10, 2),
    data_solicitacao DATETIME,
    data_atualizacao DATETIME,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (espaco_id) REFERENCES espacos_comuns(id),
    FOREIGN KEY (morador_id) REFERENCES moradores(id),
    FOREIGN KEY (aprovado_por) REFERENCES usuarios(id)
);

-- Criar tabela lista_convidados
CREATE TABLE IF NOT EXISTS lista_convidados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL,
    nome_completo VARCHAR(200) NOT NULL,
    documento VARCHAR(50),
    data_nascimento DATE,
    presente BOOLEAN DEFAULT 0,
    data_entrada DATETIME,
    data_saida DATETIME,
    data_cadastro DATETIME,
    FOREIGN KEY (reserva_id) REFERENCES reservas_espacos(id)
);

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_espacos_comuns_tenant_id ON espacos_comuns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_espacos_comuns_ativo ON espacos_comuns(ativo);
CREATE INDEX IF NOT EXISTS idx_reservas_espacos_tenant_id ON reservas_espacos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reservas_espacos_espaco_id ON reservas_espacos(espaco_id);
CREATE INDEX IF NOT EXISTS idx_reservas_espacos_morador_id ON reservas_espacos(morador_id);
CREATE INDEX IF NOT EXISTS idx_reservas_espacos_status ON reservas_espacos(status);
CREATE INDEX IF NOT EXISTS idx_lista_convidados_reserva_id ON lista_convidados(reserva_id);

