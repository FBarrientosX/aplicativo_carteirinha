# Arquivos que Configuram o Sidebar e Botão Hamburger do Módulo da Piscina

## 📁 Arquivos Principais

### 1. **Template Base (Sidebar Container)**
**Arquivo:** `app/templates/base_sidebar.html`
- **Função:** Template base que contém a estrutura HTML do sidebar e o botão hamburger
- **Conteúdo:**
  - Estrutura HTML do header com botão hamburger (`#sidebarToggle`)
  - Estrutura HTML do sidebar (`#sidebar`)
  - JavaScript que controla o toggle do sidebar (linhas 131-243)
  - Lógica de colapsar/expandir em mobile e desktop

### 2. **CSS Principal (Estilos do Sidebar)**
**Arquivo:** `app/static/css/style.css`
- **Função:** Define todos os estilos CSS do sidebar e botão hamburger
- **Seções relevantes:**
  - `.sidebar` (linha ~189-203): Estilos base da sidebar
  - `.sidebar.collapsed` (linha ~212-216): Estilos quando colapsada
  - `.sidebar-toggle` (linha ~39-63): Estilos do botão hamburger
  - `@media (max-width: 768px)` (linha ~379-424): Regras responsivas para mobile
  - `@media (min-width: 769px)` (linha ~211-217): Regras para desktop

### 3. **Navegação do Módulo Piscina**
**Arquivo:** `app/templates/navigation/sidebar_nav.html`
- **Função:** Define o conteúdo do menu lateral para o módulo da piscina
- **Seção relevante:** Linhas 4-61 (macro `render_sidebar_nav` com `current_module == 'piscina'`)
- **Itens do menu:**
  - Controle de Acesso
  - Moradores
  - Carteirinhas
  - Scanner QR
  - Salva-vidas
  - Histórico
  - Histórico por Unidade

### 4. **CSS Específico do Módulo Piscina**
**Arquivo:** `app/static/css/piscina-module.css`
- **Função:** Estilos CSS específicos para o módulo da piscina (pode ter estilos que afetam o layout geral)

### 5. **Templates que Usam o Sidebar do Módulo Piscina**

Todos os templates abaixo estendem `base_sidebar.html` e usam a navegação do módulo piscina:

#### 5.1. **Controle de Acesso**
- `app/templates/acesso/index.html` - Página principal do controle de acesso
- `app/templates/acesso/registrar.html` - Registrar entrada/saída manual

#### 5.2. **Histórico**
- `app/templates/acesso/historico.html` - Histórico geral
- `app/templates/acesso/historico_morador.html` - Histórico por morador
- `app/templates/acesso/historico_unidade.html` - Histórico por unidade

#### 5.3. **Scanner QR**
- `app/templates/acesso/qrcode.html` - Scanner de QR Code

#### 5.4. **Moradores**
- `app/templates/moradores/listar.html` - Lista de moradores
- `app/templates/moradores/carteirinhas_lote.html` - Carteirinhas em lote

#### 5.5. **Salva-vidas**
- `app/templates/salva_vidas/listar.html` - Lista de salva-vidas

---

## 🔧 Estrutura de Funcionamento

### Fluxo de Renderização:
1. **Template da página** (ex: `acesso/index.html`) estende `base_sidebar.html`
2. **Template base** (`base_sidebar.html`) renderiza:
   - Header com botão hamburger (`#sidebarToggle`)
   - Sidebar container (`#sidebar`)
   - JavaScript de controle
3. **Macro de navegação** (`sidebar_nav.html`) é chamada via `{% block sidebar_nav %}`
4. **CSS** (`style.css`) aplica estilos e responsividade

### Elementos HTML-Chave:
- **Botão Hamburger:** `<button id="sidebarToggle" class="sidebar-toggle">`
- **Sidebar:** `<aside id="sidebar" class="sidebar">`
- **Main Content:** `<main class="main-content">`

### Classes CSS Importantes:
- `.sidebar` - Sidebar base
- `.sidebar.collapsed` - Sidebar escondida
- `.sidebar-toggle` - Botão hamburger
- `.main-content.expanded` - Conteúdo quando sidebar está colapsada

---

## 📝 Para Corrigir Problemas:

1. **Botão não aparece:** Verificar `app/static/css/style.css` (`.sidebar-toggle`)
2. **Sidebar não colapsa:** Verificar JavaScript em `app/templates/base_sidebar.html` (linhas 131-243)
3. **Sidebar não aparece em mobile:** Verificar `@media (max-width: 768px)` em `app/static/css/style.css`
4. **Menu não renderiza:** Verificar `app/templates/navigation/sidebar_nav.html` (linhas 4-61)

