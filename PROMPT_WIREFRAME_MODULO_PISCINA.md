# PROMPT PARA IA DE WIREFRAMES - MÓDULO DE PISCINA

## DESCRIÇÃO GERAL DO MÓDULO

O módulo "Controle de Piscina" é um sistema completo de gestão de acesso à piscina do condomínio, com funcionalidades de controle de entrada/saída, gerenciamento de moradores, carteirinhas digitais, scanner QR Code, sistema de salva-vidas e histórico detalhado. O layout utiliza sidebar lateral fixa, header superior e área de conteúdo principal responsiva.

---

## ESTRUTURA GERAL DO LAYOUT

### Layout Base (aplicado a todas as páginas do módulo)

**Estrutura de 3 colunas:**
1. **Header Superior (fixo no topo)**
2. **Sidebar Lateral Esquerda (fixa, 280px de largura)**
3. **Área de Conteúdo Principal (flexível, ocupa largura restante)**

**Background geral:** #f8f9fa (cinza muito claro)

---

## 1. HEADER SUPERIOR

### Posicionamento
- **Posição**: Fixo no topo da página
- **Largura**: 100% da largura da tela
- **Altura**: ~60px
- **Background**: Branco (#ffffff)
- **Sombra**: 0 2px 4px rgba(0,0,0,0.1)

### Estrutura Interna (3 seções horizontais)

**Seção Esquerda:**
- **Botão Toggle Sidebar**: Ícone hambúrguer (fa-bars), alinhado à esquerda
- **Título do Sistema**: "CondoTech Solutions" com ícone de prédio (fa-building) em azul (#3498db)
- **Espaçamento**: Gap de 0.5rem entre elementos

**Seção Centro:**
- **Barra de Pesquisa**: Container com background cinza claro (#f8f9fa)
- **Ícone de busca**: Ícone de lupa (fa-search) à esquerda do input
- **Input de pesquisa**: Placeholder "Pesquisar...", borda arredondada, padding interno confortável
- **Largura**: ~400px (máximo), centralizada

**Seção Direita:**
- **Botão de Notificações**: Ícone de sino (fa-bell) com badge vermelho "3" no canto superior direito
- **Avatar do Usuário**: Imagem circular 32x32px, background azul com inicial do nome em branco
- **Nome do Usuário**: Texto ao lado do avatar, fonte média, cor escura
- **Espaçamento**: Gap de 0.75rem entre elementos

---

## 2. SIDEBAR LATERAL

### Posicionamento e Dimensões
- **Posição**: Fixa à esquerda, abaixo do header
- **Largura**: 280px (fixa)
- **Altura**: calc(100vh - 60px) (altura total menos header)
- **Background**: Azul escuro (#1e293b) ou cinza escuro (#2c3e50)
- **Cor do texto**: Branco (#ffffff)
- **Colapsável**: Botão toggle no header permite ocultar/mostrar

### Estrutura da Navegação

**Cabeçalho da Seção:**
- **Ícone**: Piscina (fa-swimming-pool) em azul claro (#3498db), tamanho 1.2rem
- **Título**: "Controle de Piscina" em fonte semibold, tamanho 1rem
- **Padding**: 1rem 1.5rem
- **Background**: Sutil diferença de tom ou border-bottom

**Menu de Navegação (7 itens):**
Lista vertical de links, cada item contém:
- **Ícone**: À esquerda, tamanho 1rem, cor branca
- **Texto**: Descrição do item, fonte regular, tamanho 0.95rem
- **Estado Ativo**: Background azul claro (#3498db) ou highlight na borda esquerda (4px)
- **Hover**: Background ligeiramente mais claro ou borda à esquerda

**Itens do Menu (ordem):**
1. **Controle de Acesso** (ícone: eye) - Primeira página, página inicial do módulo
2. **Moradores** (ícone: users) - Gerenciamento de moradores
3. **Carteirinhas** (ícone: id-card) - Geração de carteirinhas
4. **Scanner QR** (ícone: qrcode) - Leitor de QR Code
5. **Salva-vidas** (ícone: life-ring) - Equipe de salva-vidas
6. **Histórico** (ícone: history) - Histórico completo de acessos
7. **Histórico por Unidade** (ícone: building) - Histórico agrupado por unidade

**Link Inferior:**
- **"Voltar ao Dashboard"** (ícone: home)
- Posicionado no rodapé da sidebar
- Estilo diferenciado (borda superior ou background diferente)

---

## 3. ÁREA DE CONTEÚDO PRINCIPAL

### Posicionamento
- **Margem Esquerda**: 280px (largura da sidebar)
- **Padding**: 1.5rem - 2rem (responsivo)
- **Background**: #f8f9fa
- **Largura Máxima**: 100% da largura disponível

### Container Principal
- **Container-fluid**: Ocupa toda largura disponível
- **Max-width**: Sem limite (usa 100% da área disponível)
- **Padding lateral**: 2rem (desktop), 1.5rem (tablet), 1rem (mobile)

---

## PÁGINA 1: CONTROLE DE ACESSO (Página Inicial)

### Header da Página
**Layout**: Flexbox horizontal em telas grandes, vertical em mobile

**Lado Esquerdo:**
- **Título**: "Controle de Acesso à Piscina" (h2, 1.75rem, peso 600)
- **Ícone**: Piscina (fa-swimming-pool) em azul claro (#3498db), tamanho 1.5rem
- **Subtítulo**: "Gerencie o acesso de moradores à piscina" (texto cinza, 0.95rem)

**Lado Direito (botões de ação):**
- **Botão "QR Code"**: Azul primário (#3498db), ícone qrcode, texto branco
- **Botão "Registrar Manual"**: Verde (#27ae60), ícone plus, texto branco
- **Espaçamento**: Gap de 0.5rem entre botões
- **Responsivo**: Em mobile, botões ficam em coluna abaixo do título

### Cards de Estatísticas (4 cards horizontais)
**Layout**: Grid de 4 colunas (col-md-3), mesma altura

**Card 1 - Azul Primário (#3498db):**
- **Número Grande**: "0" (métrica dinâmica), fonte grande (2rem), branco
- **Texto**: "Na Piscina Agora", branco, fonte média
- **Ícone**: Users (fa-users, fa-2x) à direita, branco, opacidade 0.8
- **Layout interno**: Flexbox justify-content-between

**Card 2 - Verde (#27ae60):**
- **Número**: "0"
- **Texto**: "Entradas Hoje"
- **Ícone**: Sign-in-alt (fa-sign-in-alt, fa-2x) à direita

**Card 3 - Azul Claro (#17a2b8):**
- **Número**: "4" (exemplo)
- **Texto**: "Últimos Registros"
- **Ícone**: History (fa-history, fa-2x) à direita

**Card 4 - Amarelo (#f39c12):**
- **Link**: "Relatórios" com ícone chart-line
- **Texto**: "Ver Histórico"
- **Sem ícone lateral** (apenas link clicável)

**Estilo dos Cards:**
- Border-radius: 12px
- Padding interno: 1.5rem
- Sombra: 0 2px 8px rgba(0,0,0,0.08)
- Texto branco em todos

### Seção Principal (2 colunas lado a lado)

**Coluna Esquerda - Card "Moradores na Piscina":**
- **Header do Card**: Background azul primário (#3498db), texto branco
  - **Título**: "Moradores na Piscina (0)" com ícone users
  - **Padding**: 1rem 1.5rem
- **Conteúdo**:
  - **Se houver moradores**: Lista de itens (list-group)
    - Cada item mostra:
      - Nome do morador (h6, negrito)
      - Bloco-Apartamento (texto pequeno, cinza)
      - Botão "Saída" (vermelho outline)
      - Botão "Histórico" (azul outline, ícone history)
  - **Se não houver**: Estado vazio
    - Ícone grande de piscina (fa-3x, cinza, opacidade 0.3)
    - Texto: "Nenhum morador na piscina no momento"
    - Centralizado vertical e horizontalmente

**Coluna Direita - Card "Últimos Registros":**
- **Header do Card**: Background azul claro (#17a2b8), texto branco
  - **Título**: "Últimos Registros" com ícone history
- **Conteúdo**:
  - **Se houver registros**: Lista de itens
    - Cada registro mostra:
      - Nome do morador (h6)
      - Badge colorido (verde para Entrada, vermelho para Saída)
      - Texto: "via Qr_code - [Nome do Guardião]"
      - Permanência (se saída): "Permanência: 0:06:48" em azul
      - Timestamp: Hora (20:09) e Data (07/07) alinhados à direita
  - **Botão no rodapé**: "Ver Histórico Completo" (azul outline)
  - **Se não houver**: Estado vazio similar ao card esquerdo

**Estilo dos Cards:**
- Border-radius: 12px
- Sombra: 0 2px 8px rgba(0,0,0,0.08)
- Background: Branco

### Seção "Ações Rápidas" (abaixo das colunas)
**Card com Header:**
- **Título**: "Ações Rápidas" com ícone bolt (fa-bolt)
- **Background header**: Cinza claro (#f8f9fa)

**Grid de 4 botões grandes:**
1. **Leitor QR Code**: Azul outline, ícone qrcode (fa-2x), texto "Acesso automático"
2. **Registro Manual**: Verde outline, ícone edit (fa-2x), texto "Entrada/saída manual"
3. **Relatórios**: Azul claro outline, ícone chart-line (fa-2x), texto "Histórico e estatísticas"
4. **Moradores**: Amarelo outline, ícone users (fa-2x), texto "Gerenciar carteirinhas"

**Estilo dos Botões:**
- Largura total (w-100)
- Altura total (h-100)
- Layout vertical (flex-column)
- Centralizado (justify-content-center, align-items-center)
- Padding vertical: 1.5rem
- Border-radius: 8px

---

## PÁGINA 2: MORADORES

### Header da Página
**Estrutura similar à página 1:**
- **Título**: "Moradores" (h2, ícone users em azul claro)
- **Subtítulo**: "Gerencie moradores e dependentes"
- **Botão**: "Novo Morador" (azul primário, ícone plus)

### Seção de Filtros
**Card com Header:**
- **Título**: "Filtros" com ícone filter

**Grid de Filtros (4 colunas):**
1. **Bloco**: Select dropdown (col-lg-2)
2. **Status**: Select dropdown (col-lg-2)
3. **Busca**: Input de texto (col-lg-4), placeholder "Digite o nome do morador"
4. **Botões**: "Filtrar" (azul) e espaço para "Limpar" se necessário (col-lg-4)

**Estilo dos Filtros:**
- Labels acima dos campos
- Campos com border-radius: 8px
- Alinhamento vertical: align-items-end
- Gap: 1rem entre campos

### Seção de Lista
**Card com Header:**
- **Título**: "Lista de Moradores (X encontrados)"

**Tabela com colunas:**
- Nome
- Bloco/Apt
- Status (badge colorido)
- Vencimento
- Telefone
- Ações (coluna fixa de 180px)

**Ações por linha:**
- Botão "Ver" (azul outline)
- Botão "Editar" (amarelo outline)
- Botão "Carteirinha" (verde outline)
- Botão "Excluir" (vermelho outline)

**Pagination**: Abaixo da tabela, centralizada

---

## PÁGINA 3: CARTEIRINHAS

### Header da Página
- **Título**: "Gerar Carteirinhas em Lote" (ícone id-card-alt)
- **Subtítulo**: "Selecione os moradores para gerar carteirinhas"
- **Botão**: "Voltar para Moradores" (outline-secondary)

### Seção de Seleção
**Card com Header:**
- **Título**: "Selecionar Moradores (X disponíveis)"
- **Botões no header**: "Selecionar Todos" e "Limpar Seleção"

**Alerta Informativo:**
- Background azul claro
- Texto: "X moradores selecionados" (dinâmico)
- Ícone info-circle

**Tabela com checkboxes:**
- Coluna checkbox (50px)
- Morador
- Apartamento
- Validade
- Status
- Ações (100px)

**Botões de Ação:**
- "Gerar Carteirinhas Selecionadas" (azul primário, grande)
- "Gerar PDF" ou "Gerar Imagens" (secundário)

---

## PÁGINA 4: SCANNER QR CODE

### Header da Página
- **Título**: "Leitor QR Code" (ícone qrcode)
- **Subtítulo**: "Escaneie ou digite o código QR da carteirinha"
- **Botão**: "Voltar" (outline-secondary)

### Seção de Busca
**Card com Header:**
- **Título**: "Buscar Morador"

**Formulário:**
- **Campo 1**: "Código QR ou ID" (input grande, col-lg-6)
  - Placeholder: "Cole o código QR aqui ou digite o ID"
  - Texto de ajuda: "Escaneie o QR Code da carteirinha ou digite o ID do morador"
- **Campo 2**: "Buscar por Nome" (input, col-lg-4)
  - Placeholder: "Nome do morador"
- **Botões**: "Enviar QR" (azul) e "Buscar" (azul outline, col-lg-2)

### Seção de Resultados
**Card com resultados:**
- **Se encontrado**: Lista de moradores com:
  - Foto do morador (circular)
  - Nome completo
  - Bloco-Apartamento
  - Status da carteirinha
  - Botões de ação: "Registrar Entrada" e "Registrar Saída"
- **Se não encontrado**: Alerta de erro ou mensagem informativa

---

## PÁGINA 5: SALVA-VIDAS

### Header da Página
- **Título**: "Equipe de Salva-vidas" (ícone life-ring)
- **Subtítulo**: "Gerencie a equipe de salva-vidas"
- **Botão**: "Novo Salva-vidas" (azul primário)

### Cards de Estatísticas (4 cards)
1. **Total**: Ícone users, número grande, texto "Total"
2. **Ativos**: Ícone check-circle verde, número, texto "Ativos"
3. **Inativos**: Ícone pause-circle amarelo, número, texto "Inativos"
4. **Certificados**: Ícone certificate azul, número, texto "Certificados"

**Estilo**: Cards brancos, ícones fa-2x, centralizados

### Seção de Filtros
Similar à página de Moradores

### Seção de Lista
**Tabela com colunas:**
- Nome
- CPF
- Status (badge)
- Certificações
- Telefone
- Ações

---

## PÁGINA 6: HISTÓRICO

### Header da Página
- **Título**: "Histórico de Acessos" (ícone history)
- **Subtítulo**: "Visualize o histórico completo de acessos à piscina"
- **Botões**: "Exportar CSV" (verde) e "Voltar" (outline-secondary)

### Seção de Filtros
**Card com Header**: "Filtros"

**Grid de Filtros (5 campos):**
1. **Morador**: Select dropdown (col-md-3)
2. **Data Início**: Input date (col-md-2)
3. **Data Fim**: Input date (col-md-2)
4. **Tipo**: Select (Entrada/Saída/Todos) (col-md-2)
5. **Botões**: "Filtrar" (azul) e "Limpar" (cinza) (col-md-3)

### Seção de Tabela
**Card com tabela:**
- **Colunas**: Data/Hora, Morador, Tipo (badge), Método, Guardião, Ações
- **Badges**: Verde para Entrada, Vermelho para Saída
- **Pagination**: Abaixo da tabela

---

## PÁGINA 7: HISTÓRICO POR UNIDADE

### Header da Página
- **Título**: "Histórico de Acessos por Unidade" (ícone building)
- **Subtítulo**: "Visualize o histórico de acessos agrupado por unidade"
- **Botões**: "Exportar CSV" (verde), "Histórico Completo" (cinza), "Voltar" (outline-secondary)

### Seção de Filtros
**Grid de Filtros:**
- **Bloco**: Select (col-lg-2)
- **Apartamento**: Input texto (col-lg-2)
- **Data Início**: Input date (col-lg-2)
- **Data Fim**: Input date (col-lg-2)
- **Botões**: "Filtrar" e "Limpar" (col-lg-4)

### Seção de Resultados
**Cards agrupados por unidade:**
- Cada card representa uma unidade (Bloco-Apartamento)
- **Header do card**: Nome da unidade, total de entradas/saídas
- **Conteúdo**: Lista de registros dessa unidade
- **Expandir/Colapsar**: Opcional, para ver mais detalhes

---

## ESPECIFICAÇÕES DE DESIGN

### Cores Principais
- **Azul Primário**: #3498db
- **Azul Claro**: #17a2b8
- **Verde**: #27ae60
- **Vermelho**: #e74c3c
- **Amarelo**: #f39c12
- **Cinza Escuro**: #2c3e50
- **Cinza Médio**: #6c757d
- **Cinza Claro**: #f8f9fa
- **Branco**: #ffffff

### Tipografia
- **Font-family**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **Títulos h2**: 1.75rem, peso 600, cor #2c3e50
- **Subtítulos**: 0.95rem, cor #6c757d
- **Texto normal**: 0.9375rem, cor #2c3e50
- **Texto pequeno**: 0.85rem, cor #6c757d

### Espaçamentos
- **Padding cards**: 1.5rem - 2rem
- **Margin entre seções**: 1.5rem - 2rem
- **Gap entre elementos**: 0.5rem - 1rem
- **Border-radius**: 8px - 12px

### Componentes Bootstrap
- Cards, Buttons, Badges, List Groups, Alerts, Tables
- Grid System (container-fluid, row, col-*)
- Flexbox utilities
- Spacing utilities

### Ícones
- **Biblioteca**: Font Awesome 6.0.0
- **Estilo**: Solid (fas)
- **Tamanhos**: fa-2x, fa-3x, fa-4x conforme contexto

### Responsividade
- **Desktop (≥992px)**: Sidebar sempre visível, layout horizontal
- **Tablet (768-991px)**: Sidebar colapsável, layout adaptável
- **Mobile (<768px)**: Sidebar overlay, layout vertical, botões em coluna

---

## ESTADOS E INTERAÇÕES

### Estados dos Elementos
- **Hover**: Elevação de cards (transform: translateY(-2px)), sombra aumentada
- **Active**: Background colorido ou borda destacada
- **Disabled**: Opacidade reduzida, cursor not-allowed
- **Loading**: Spinner ou skeleton screens

### Transições
- **Transição de cards**: 0.3s ease
- **Transição de sidebar**: 0.3s ease
- **Transição de botões**: 0.2s ease

---

## OBSERVAÇÕES PARA O WIREFRAME

1. **Hierarquia Visual**: Títulos destacados, subtítulos em cinza, espaçamento generoso
2. **Consistência**: Mesmo padrão visual em todas as páginas
3. **Usabilidade**: Elementos clicáveis bem definidos, feedback visual claro
4. **Responsividade**: Considerar diferentes tamanhos de tela
5. **Acessibilidade**: Contraste adequado, elementos focáveis claros
6. **Navegação**: Sidebar sempre acessível, breadcrumbs opcionais
7. **Feedback**: Mensagens de sucesso/erro claras, estados de loading

---

## FLUXO DE NAVEGAÇÃO

1. **Entrada no módulo**: Usuário acessa "Controle de Acesso" (primeira aba)
2. **Navegação lateral**: Sidebar permite acesso rápido a todas as abas
3. **Breadcrumbs**: Opcional, mostrar "Dashboard > Controle de Piscina > [Aba Atual]"
4. **Links de retorno**: Botões "Voltar" ou links contextuais para navegação rápida
5. **Ações rápidas**: Cards de ação rápida na página inicial para acesso direto a funcionalidades

---

## DETALHES ESPECÍFICOS POR COMPONENTE

### Cards de Estatísticas
- Altura mínima: 120px
- Padding interno: 1.5rem
- Ícones sempre à direita
- Números grandes e destacados
- Texto descritivo abaixo

### Tabelas
- Striped rows (cores alternadas)
- Hover effect em linhas
- Coluna de ações fixa à direita
- Badges coloridos para status
- Pagination abaixo da tabela

### Formulários
- Labels acima dos campos
- Campos com border-radius: 8px
- Focus state: borda azul, sombra sutil
- Botões de ação alinhados à direita
- Mensagens de validação abaixo dos campos

### Listas
- List-group estilo Bootstrap
- Items com padding confortável
- Dividers sutis entre itens
- Ações à direita de cada item
- Estados vazios com ícones grandes e mensagens

---

Este prompt fornece todas as informações necessárias para criar wireframes detalhados e precisos do módulo de piscina e todas as suas abas.

