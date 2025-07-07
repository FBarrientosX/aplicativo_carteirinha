# Sistema de Controle de Acesso à Piscina

## Visão Geral

O Sistema de Controle de Acesso à Piscina é uma funcionalidade completa integrada ao sistema de carteirinhas que permite registrar e monitorar entradas e saídas dos moradores na piscina do condomínio.

## Funcionalidades Implementadas

### 1. Dashboard de Controle de Acesso
- **Rota**: `/acesso-piscina`
- **Funcionalidades**:
  - Visualização de moradores atualmente na piscina
  - Estatísticas em tempo real (entradas do dia, total na piscina)
  - Últimos 10 registros de acesso
  - Ações rápidas para diferentes tipos de registro
  - Auto-refresh da página a cada 30 segundos

### 2. Leitor de QR Code
- **Rota**: `/acesso-piscina/qrcode`
- **Funcionalidades**:
  - Leitura automática de QR Code das carteirinhas
  - Busca manual por nome do morador
  - Processamento automático de entrada/saída
  - Validação de carteirinha ativa
  - Interface intuitiva com instruções de uso

### 3. Registro Manual
- **Rota**: `/acesso-piscina/registrar`
- **Funcionalidades**:
  - Formulário para registro manual de entrada/saída
  - Seleção de morador com carteirinha ativa
  - Campo obrigatório para nome do guardião
  - Observações opcionais
  - Validação de status atual (dentro/fora da piscina)

### 4. Histórico de Acessos
- **Rota**: `/acesso-piscina/historico`
- **Funcionalidades**:
  - Listagem paginada de todos os registros
  - Filtros por morador, data e tipo de acesso
  - Exportação para CSV
  - Cálculo automático de tempo de permanência
  - Visualização de método de registro (manual/QR Code)

### 5. Histórico Individual
- **Rota**: `/acesso-piscina/morador/<id>`
- **Funcionalidades**:
  - Histórico específico de um morador
  - Estatísticas individuais (total de entradas, frequência)
  - Últimos 50 registros
  - Status atual (dentro/fora da piscina)
  - Ações rápidas para o morador

## Modelo de Dados

### Tabela `registro_acesso`
```sql
CREATE TABLE registro_acesso (
    id INTEGER PRIMARY KEY,
    morador_id INTEGER NOT NULL,
    tipo VARCHAR(10) NOT NULL,          -- 'entrada' ou 'saida'
    data_hora DATETIME NOT NULL,
    metodo VARCHAR(20) NOT NULL,        -- 'manual', 'qrcode', 'barcode'
    guardiao VARCHAR(100),              -- Nome do guardião
    observacoes TEXT,
    ip_origem VARCHAR(45),              -- IP de origem do registro
    FOREIGN KEY (morador_id) REFERENCES moradores(id)
);
```

### Relacionamentos
- **RegistroAcesso** → **Morador**: Many-to-One
- Cada morador pode ter múltiplos registros de acesso
- Ordenação padrão: data_hora DESC (mais recente primeiro)

## Métodos de Acesso

### 1. QR Code (Automático)
- **Processo**:
  1. Morador apresenta carteirinha com QR Code
  2. Guardião escaneia o código
  3. Sistema decodifica JSON com dados do morador
  4. Validação automática de carteirinha ativa
  5. Determinação automática do tipo (entrada/saída)
  6. Registro instantâneo no sistema

### 2. Manual
- **Processo**:
  1. Guardião seleciona morador no formulário
  2. Escolhe tipo de acesso (entrada/saída)
  3. Informa seu nome como guardião
  4. Adiciona observações (opcional)
  5. Sistema valida e registra

### 3. Busca por Nome
- **Processo**:
  1. Guardião digita nome do morador
  2. Sistema retorna lista de moradores encontrados
  3. Seleção do morador correto
  4. Processamento automático baseado no status atual

## Validações Implementadas

### 1. Carteirinha Ativa
- Verificação se a carteirinha está ativa
- Bloqueio de acesso para carteirinhas inativas
- Mensagem de erro apropriada

### 2. Status Atual
- **Entrada**: Só permite se morador não estiver na piscina
- **Saída**: Só permite se morador estiver na piscina
- Prevenção de registros duplicados

### 3. Dados Obrigatórios
- Morador deve ser selecionado
- Tipo de acesso deve ser definido
- Nome do guardião é obrigatório (registro manual)

## Recursos Avançados

### 1. Cálculo de Permanência
- Automático para registros de saída
- Calcula tempo entre última entrada e saída
- Exibição em formato legível (horas:minutos)

### 2. Estatísticas em Tempo Real
- Contagem de moradores na piscina
- Entradas do dia atual
- Total de registros históricos
- Integração com dashboard principal

### 3. Relatórios e Exportação
- Exportação CSV com todos os dados
- Filtros avançados por período
- Paginação para grandes volumes
- Formatação apropriada para impressão

## Interface do Usuário

### 1. Design Responsivo
- Compatível com tablets e smartphones
- Interface otimizada para uso em portaria
- Botões grandes e fáceis de usar

### 2. Feedback Visual
- Badges coloridos para status (entrada/saída)
- Ícones intuitivos para cada ação
- Mensagens de sucesso/erro claras
- Loading states apropriados

### 3. Navegação Intuitiva
- Menu principal com acesso rápido
- Breadcrumbs para orientação
- Botões de voltar em todas as páginas
- Atalhos para ações frequentes

## Segurança

### 1. Rastreamento
- Registro de IP de origem
- Timestamp preciso de cada ação
- Identificação do guardião responsável

### 2. Validação de Dados
- Sanitização de inputs
- Prevenção de SQL injection
- Validação de tipos de dados

### 3. Auditoria
- Log completo de todas as ações
- Histórico imutável de registros
- Rastreabilidade completa

## Integração com Sistema Existente

### 1. Menu Principal
- Novo dropdown "Controle de Acesso"
- Acesso direto a todas as funcionalidades
- Integração com navegação existente

### 2. Dashboard Principal
- Seção dedicada com estatísticas
- Cards informativos com links diretos
- Atualização automática de dados

### 3. Perfil do Morador
- Botão direto para histórico individual
- Link para gerar carteirinha
- Status atual visível

## Casos de Uso

### 1. Entrada Normal
1. Morador chega à piscina
2. Apresenta carteirinha ao guardião
3. Guardião escaneia QR Code
4. Sistema registra entrada automaticamente
5. Morador liberado para usar piscina

### 2. Saída Normal
1. Morador sai da piscina
2. Apresenta carteirinha ao guardião
3. Guardião escaneia QR Code
4. Sistema registra saída e calcula permanência
5. Registro completo no histórico

### 3. Problema com QR Code
1. QR Code não funciona ou carteirinha esquecida
2. Guardião usa busca manual por nome
3. Seleciona morador correto
4. Registra entrada/saída manualmente
5. Adiciona observação sobre o problema

### 4. Consulta de Histórico
1. Administrador acessa relatórios
2. Filtra por morador ou período
3. Visualiza estatísticas e registros
4. Exporta dados se necessário
5. Toma decisões baseadas nos dados

## Benefícios

### 1. Para o Condomínio
- Controle preciso de uso da piscina
- Dados para tomada de decisões
- Segurança e rastreabilidade
- Relatórios para assembleia

### 2. Para os Moradores
- Processo rápido e fácil
- Histórico pessoal disponível
- Transparência no controle
- Carteirinha digital sempre disponível

### 3. Para os Guardiões
- Interface simples e intuitiva
- Múltiplas opções de registro
- Feedback imediato
- Redução de erros manuais

## Manutenção e Suporte

### 1. Backup de Dados
- Registros são permanentes
- Backup automático do banco
- Recuperação de dados históricos

### 2. Monitoramento
- Logs de sistema
- Alertas de erro
- Métricas de uso

### 3. Atualizações
- Compatibilidade com versões futuras
- Migração de dados automática
- Documentação atualizada

## Próximas Melhorias

### 1. Funcionalidades Planejadas
- Notificações por email para administradores
- Relatórios gráficos de uso
- API para integração com outros sistemas
- App mobile para guardiões

### 2. Otimizações
- Cache para consultas frequentes
- Compressão de dados históricos
- Indexação de banco de dados
- Performance de consultas

### 3. Recursos Avançados
- Reconhecimento facial
- Integração com câmeras
- Alertas de superlotação
- Controle de horários especiais

---

**Desenvolvido em**: Dezembro 2024  
**Tecnologias**: Flask, SQLAlchemy, Bootstrap, JavaScript  
**Compatibilidade**: Navegadores modernos, dispositivos móveis  
**Status**: Implementado e funcional 