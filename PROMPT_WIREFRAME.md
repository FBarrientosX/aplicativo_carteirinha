# PROMPT PARA IA DE WIREFRAMES - CondoTech Solutions

## DESCRIÇÃO GERAL DO SISTEMA

CondoTech Solutions é um sistema SaaS para gestão de condomínios, com design moderno inspirado no estilo MyCond. O sistema possui múltiplos módulos funcionais e utiliza layout responsivo com sidebar lateral, header superior e área de conteúdo principal.

---

## PÁGINA 1: DASHBOARD PRINCIPAL (PÁGINA INICIAL)

### Estrutura Geral
- **Layout**: Sem sidebar nesta página, apenas header superior e conteúdo centralizado
- **Tipo**: Página de seleção de módulos
- **Background**: Fundo claro (#f8f9fa)
- **Container**: Largura máxima centralizada, com padding lateral responsivo

### Header Superior
- **Título Principal**: 
  - Texto: "Painel Geral"
  - Ícone: Building (ícone de prédio) em azul (#3498db)
  - Tamanho: 2rem, peso 600
  - Cor: #2c3e50
- **Subtítulo**: 
  - Texto: "Que bom ter você por aqui, [Nome do Usuário]!"
  - Cor: Cinza (#6c757d)
  - Tamanho: Padrão

### Seção de Módulos
- **Título da Seção**: 
  - Texto: "Selecione um Módulo"
  - Centralizado
  - Ícone: Grid (fas fa-th-large)
  - Margem inferior: 1.5rem

- **Grid de Cards de Módulos**:
  - **Layout**: Grid responsivo com 4 colunas em telas grandes (col-lg-3), 2 colunas em tablets (col-md-6)
  - **Distribuição**: Cards centralizados horizontalmente com justify-content-center
  - **Largura dos Cards**: Máximo 280px em telas grandes
  - **Espaçamento**: Gap de 1.5rem entre cards

- **Cada Card de Módulo contém**:
  - **Borda Esquerda Colorida**: 5px sólida (cor varia por módulo)
  - **Ícone Grande**: 3.5rem, centralizado, com cor temática
  - **Título do Módulo**: 1.5rem, peso 600, centralizado
  - **Descrição**: Texto pequeno, cinza, centralizado, 2-3 linhas
  - **Lista de Funcionalidades**: 
    - 4 itens com ícones de check verde
    - Texto pequeno
    - Alinhamento à esquerda dentro do card
  - **Botão de Ação**: 
    - Botão azul primário "Acessar Módulo"
    - Ícone de play
    - Largura total (d-grid)
  - **Badge de Status**: 
    - Texto verde "Módulo Ativo"
    - Ícone de check-circle verde

- **Módulos Disponíveis** (10 no total):
  1. **Controle de Piscina** - Azul (#007bff), ícone swimming-pool
  2. **Manutenção & Chamados** - Verde (#28a745), ícone tools
  3. **Reserva de Espaços** - Azul (#007bff), ícone calendar-alt
  4. **Controle de Visitantes** - Amarelo (#ffc107), ícone user-friends
  5. **Portal de Encomendas** - Azul claro (#17a2b8), ícone box
  6. **Marketplace** - Verde (#28a745), ícone store
  7. **Ocorrências** - Vermelho (#dc3545), ícone exclamation-triangle
  8. **Achados e Perdidos** - Amarelo (#ffc107), ícone search-dollar
  9. **Votação** - Azul (#007bff), ícone vote-yea
  10. **Atividades** - Azul claro (#17a2b8), ícone calendar-check

- **Estilo dos Cards**:
  - Border-radius: 12px
  - Sombra: 0 2px 8px rgba(0, 0, 0, 0.08)
  - Hover: Elevação de 4px, sombra aumentada
  - Altura: 100% (h-100)
  - Padding interno: 2rem

### Seção Inferior (Informações da Empresa)
- **Card de Fundo Claro**:
  - 4 colunas com ícones e descrições
  - Ícones: Shield (Seguro), Cloud (Na Nuvem), Headset (Suporte), Rocket (Inovação)
  - Cores temáticas para cada ícone
  - Texto centralizado

---

## PÁGINA 2: PAINEL DO MÓDULO DE PISCINA (CONTROLE DE ACESSO)

### Estrutura Geral
- **Layout**: Sidebar lateral esquerda (280px) + Header superior + Área de conteúdo principal
- **Background**: Fundo claro (#f8f9fa)
- **Sidebar**: Fundo azul escuro (#1e293b), largura fixa 280px, colapsável

### Header Superior
- **Lado Esquerdo**:
  - Botão de toggle da sidebar (hamburger menu)
  - Título: "CondoTech Solutions" com ícone de prédio
- **Centro**:
  - Barra de pesquisa: Input com ícone de lupa, placeholder "Pesquisar..."
- **Lado Direito**:
  - Ícone de notificações (sino) com badge vermelho "3"
  - Avatar do usuário (32x32px)
  - Nome do usuário: "Administrador do Sistema"

### Sidebar Lateral (Esquerda)
- **Título da Seção**: "Controle de Piscina" com ícone de piscina
- **Menu de Navegação** (7 itens):
  1. **Controle de Acesso** (ativo) - Ícone eye, azul claro
  2. **Moradores** - Ícone users
  3. **Carteirinhas** - Ícone id-card
  4. **Scanner QR** - Ícone qrcode
  5. **Salva-vidas** - Ícone life-ring
  6. **Histórico** - Ícone history
  7. **Histórico por Unidade** - Ícone building
- **Link Inferior**: "Voltar ao Dashboard" com ícone de casa

### Área de Conteúdo Principal

#### Header da Página
- **Layout**: Flexbox horizontal em telas grandes, vertical em mobile
- **Lado Esquerdo**:
  - Título: "Controle de Acesso à Piscina" (h2, azul #3498db)
  - Ícone: Swimming-pool em azul claro
  - Subtítulo: "Gerencie o acesso de moradores à piscina" (cinza)
- **Lado Direito** (botões):
  - Botão Azul: "QR Code" com ícone qrcode
  - Botão Verde: "Registrar Manual" com ícone plus
  - Espaçamento: Gap de 0.5rem entre botões

#### Cards de Estatísticas (4 cards horizontais)
- **Layout**: Grid de 4 colunas (col-md-3), mesma altura
- **Card 1 - Azul (Primary)**:
  - Número grande: "0" (métrica)
  - Texto: "Na Piscina Agora"
  - Ícone: Users (fa-2x) à direita
- **Card 2 - Verde (Success)**:
  - Número: "0"
  - Texto: "Entradas Hoje"
  - Ícone: Sign-in-alt (fa-2x)
- **Card 3 - Azul Claro (Info)**:
  - Número: "4"
  - Texto: "Últimos Registros"
  - Ícone: History (fa-2x)
- **Card 4 - Amarelo (Warning)**:
  - Link: "Relatórios" com ícone chart-line
  - Texto: "Ver Histórico"
  - Sem ícone lateral

#### Seção Principal (2 colunas lado a lado)

**Coluna Esquerda - Card "Moradores na Piscina"**:
- **Header do Card**: Azul primário, texto branco
  - Título: "Moradores na Piscina (0)"
  - Ícone: Users
- **Conteúdo**:
  - **Se houver moradores**: Lista de itens com:
    - Nome do morador (h6)
    - Bloco-Apartamento (texto pequeno cinza)
    - Botões: "Saída" (vermelho outline) e "Histórico" (azul outline)
  - **Se não houver**: Estado vazio
    - Ícone grande de piscina (fa-3x, cinza)
    - Texto: "Nenhum morador na piscina no momento"

**Coluna Direita - Card "Últimos Registros"**:
- **Header do Card**: Azul claro (info), texto branco
  - Título: "Últimos Registros"
  - Ícone: History
- **Conteúdo**:
  - **Se houver registros**: Lista de itens com:
    - Nome do morador (h6)
    - Badge colorido (verde para Entrada, vermelho para Saída)
    - Método: "via Qr_code - [Nome do Guardião]"
    - Permanência (se saída): "Permanência: 0:06:48"
    - Timestamp: Hora (20:09) e Data (07/07) alinhados à direita
  - **Botão no rodapé**: "Ver Histórico Completo" (azul outline)
  - **Se não houver**: Estado vazio
    - Ícone grande de history (fa-3x, cinza)
    - Texto: "Nenhum registro encontrado"

#### Seção "Ações Rápidas" (abaixo das colunas)
- **Card com Header**: Título "Ações Rápidas" com ícone bolt
- **Grid de 4 botões grandes**:
  1. **Leitor QR Code** - Azul outline, ícone qrcode (fa-2x), texto "Acesso automático"
  2. **Registro Manual** - Verde outline, ícone edit (fa-2x), texto "Entrada/saída manual"
  3. **Relatórios** - Azul claro outline, ícone chart-line (fa-2x), texto "Histórico e estatísticas"
  4. **Moradores** - Amarelo outline, ícone users (fa-2x), texto "Gerenciar carteirinhas"
- **Cada botão**: Altura total (h-100), layout vertical (flex-column), centralizado

### Estilos Visuais
- **Cards**: Border-radius 12px, sombra suave, hover com elevação
- **Cores Principais**:
  - Azul primário: #3498db
  - Azul escuro: #2c3e50
  - Verde: #27ae60
  - Vermelho: #e74c3c
  - Amarelo: #f39c12
- **Tipografia**: 
  - Font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
  - Títulos: Peso 600
  - Textos: Tamanho padrão, cor #2c3e50
- **Espaçamentos**: Padding de 1.5rem-2rem em cards, gap de 1rem entre elementos

### Responsividade
- **Desktop (≥992px)**: Sidebar sempre visível, layout horizontal
- **Tablet (768-991px)**: Sidebar colapsável, layout adaptável
- **Mobile (<768px)**: Sidebar overlay, layout vertical

---

## ESPECIFICAÇÕES TÉCNICAS

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 991px
- Desktop: 992px - 1399px
- Large Desktop: ≥ 1400px
- Extra Large: ≥ 1920px

### Componentes Bootstrap Utilizados
- Cards, Buttons, Badges, List Groups, Alerts
- Grid System (container-fluid, row, col-*)
- Flexbox utilities (d-flex, justify-content-*, align-items-*)
- Spacing utilities (mb-*, mt-*, p-*, gap-*)

### Ícones
- Biblioteca: Font Awesome 6.0.0
- Estilo: Solid (fas)
- Tamanhos: fa-2x, fa-3x, fa-4x conforme contexto

---

## OBSERVAÇÕES PARA O WIREFRAME

1. **Foco na usabilidade**: Layout limpo e intuitivo
2. **Hierarquia visual clara**: Títulos destacados, subtítulos em cinza
3. **Espaçamento generoso**: Não sobrecarregar a interface
4. **Consistência**: Mesmo padrão visual em ambas as páginas
5. **Responsividade**: Considerar diferentes tamanhos de tela
6. **Acessibilidade**: Contraste adequado, elementos clicáveis bem definidos

