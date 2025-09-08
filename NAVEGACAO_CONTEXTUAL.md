# Sistema de Navegação Contextual por Módulos

## Visão Geral

O CondoTech Solutions agora implementa um sistema de navegação contextual que adapta os menus de acordo com o módulo que o usuário está utilizando. Isso melhora significativamente a experiência do usuário ao mostrar apenas as opções relevantes para cada contexto.

## Funcionalidades Implementadas

### 1. Navegação Modular
- **Módulo Piscina**: Moradores, Carteirinhas, Scanner QR, Controle de Acesso, Salva-vidas, Histórico
- **Módulo Manutenção**: Dashboard, Lista de Chamados, Novo Chamado, Categorias, Relatórios
- **Módulo Admin**: Dashboard Admin, Condomínios, Módulos, Info Sistema
- **Módulo Usuários**: Listar Usuários, Novo Usuário, Permissões
- **Módulo Configurações**: Condomínio, Email, Sistema, Relatórios, Logs
- **Módulo Salva-vidas**: Dashboard, Scanner QR, Registrar Acesso, Na Piscina

### 2. Breadcrumb Contextual
- Navegação hierárquica clara
- Indicação visual do módulo atual
- Links para voltar ao dashboard principal

### 3. Cores por Módulo
- **Piscina**: Azul (Info)
- **Manutenção**: Verde (Success)
- **Admin**: Vermelho (Danger)
- **Usuários**: Amarelo (Warning)
- **Configurações**: Cinza (Secondary)
- **Salva-vidas**: Azul Primário (Primary)

## Arquivos Criados/Modificados

### 1. Template de Navegação
- `app/templates/navigation/module_nav.html`
  - Macro `render_module_nav()` para navegação contextual
  - Macro `render_breadcrumb()` para breadcrumb
  - Suporte responsivo para dispositivos móveis

### 2. Templates Atualizados
#### Módulo Piscina:
- `app/templates/moradores/listar.html`
- `app/templates/moradores/carteirinhas_lote.html`
- `app/templates/acesso/index.html`

#### Módulo Manutenção:
- `app/templates/manutencao/dashboard.html`
- `app/templates/manutencao/listar_chamados.html`

#### Módulo Admin:
- `app/templates/admin/dashboard.html`

#### Módulo Configurações:
- `app/templates/configuracoes/index.html`

### 3. Estilos CSS
- `app/static/css/style.css`
  - Estilos para navegação contextual
  - Cores específicas por módulo
  - Responsividade para dispositivos móveis

## Como Usar

### 1. Em Templates Existentes
```html
{% extends "base.html" %}
{% from 'navigation/module_nav.html' import render_module_nav, render_breadcrumb %}

{% block content %}
<!-- Navegação contextual do módulo -->
{{ render_module_nav('piscina', 'moradores') }}
{{ render_breadcrumb('piscina', 'moradores', 'Moradores') }}

<!-- Conteúdo da página -->
<div class="container">
    <!-- ... -->
</div>
{% endblock %}
```

### 2. Parâmetros das Macros

#### render_module_nav(current_module, current_page)
- `current_module`: Nome do módulo ('piscina', 'manutencao', 'admin', etc.)
- `current_page`: Página atual dentro do módulo ('moradores', 'dashboard', etc.)

#### render_breadcrumb(current_module, current_page, page_title)
- `current_module`: Nome do módulo
- `current_page`: Página atual
- `page_title`: Título específico da página (opcional)

## Módulos Disponíveis

1. **piscina**: Controle de Piscina
2. **manutencao**: Manutenção & Chamados
3. **admin**: Administração do Sistema
4. **usuarios**: Gestão de Usuários
5. **configuracoes**: Configurações do Sistema
6. **salva_vidas**: Módulo Salva-vidas

## Características Técnicas

### 1. Responsividade
- Navegação adaptativa para dispositivos móveis
- Scroll horizontal em telas pequenas
- Textos abreviados em dispositivos móveis

### 2. Acessibilidade
- Ícones Font Awesome para identificação visual
- Cores contrastantes para melhor legibilidade
- Navegação por teclado suportada

### 3. Performance
- CSS otimizado com transições suaves
- Carregamento rápido dos estilos
- Estrutura HTML semântica

## Próximos Passos

1. **Expandir para Mais Templates**: Aplicar navegação contextual em todos os templates dos módulos
2. **Permissões por Módulo**: Ocultar navegação de módulos inativos para o tenant
3. **Customização por Tenant**: Permitir personalização das cores por condomínio
4. **Analytics de Navegação**: Implementar tracking de uso dos módulos
5. **Navegação por Voz**: Adicionar suporte para comandos de voz (futuro)

## Benefícios

### Para Usuários:
- **Foco**: Veem apenas opções relevantes ao contexto atual
- **Eficiência**: Navegação mais rápida e intuitiva
- **Clareza**: Identificação visual clara do módulo ativo

### Para Desenvolvedores:
- **Manutenibilidade**: Código organizado em macros reutilizáveis
- **Escalabilidade**: Fácil adição de novos módulos
- **Consistência**: Padrão visual uniforme em todo o sistema

### Para o Negócio:
- **Experiência do Usuário**: Interface mais profissional e moderna
- **Adoção**: Usuários encontram funcionalidades mais facilmente
- **Diferenciação**: Destaque competitivo no mercado

## Suporte

Para dúvidas ou sugestões sobre o sistema de navegação contextual, consulte a documentação técnica ou entre em contato com a equipe de desenvolvimento.

---
**CondoTech Solutions** - Tecnologia que simplifica a vida no condomínio
