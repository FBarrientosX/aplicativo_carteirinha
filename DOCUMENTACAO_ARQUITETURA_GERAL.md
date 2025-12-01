# 🏗️ Documentação de Arquitetura Geral - CondoTech Solutions

## 📋 ÍNDICE

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Fluxo de Autenticação e Acesso](#2-fluxo-de-autenticação-e-acesso)
3. [Estrutura de Navegação](#3-estrutura-de-navegação)
4. [Módulos do Sistema](#4-módulos-do-sistema)
5. [Hierarquia de Usuários e Permissões](#5-hierarquia-de-usuários-e-permissões)
6. [Design System e Padrões Visuais](#6-design-system-e-padrões-visuais)
7. [Melhorias e Boas Práticas](#7-melhorias-e-boas-práticas)

---

## 1. VISÃO GERAL DO SISTEMA

### 1.1 Conceito

O **CondoTech Solutions** é uma plataforma SaaS multi-tenant para gestão completa de condomínios, oferecendo diversos módulos integrados que facilitam o dia a dia de administradores, moradores e funcionários.

### 1.2 Arquitetura de Navegação

```
┌─────────────────────────────────────────────────────────────┐
│                    TELA DE LOGIN                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Usuário: [___________]                                │  │
│  │  Senha:   [___________]                                │  │
│  │  ☐ Lembrar de mim                                      │  │
│  │  [Entrar]                                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   VERIFICAÇÃO DE PERMISSÕES    │
        └───────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│  ADMIN        │              │  SALVA-VIDAS     │
│  Dashboard    │              │  Dashboard       │
│  (Módulos)    │              │  (Simplificado)   │
└───────────────┘              └──────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   NAVEGAÇÃO POR MÓDULOS        │
        │   (Sidebar + Header)           │
        └───────────────────────────────┘
```

### 1.3 Estrutura de Módulos

O sistema é composto por módulos independentes mas integrados:

1. **🏊 Controle de Piscina** - Sistema completo de acesso e carteirinhas
2. **📅 Reserva de Espaços** - Reserva de áreas comuns
3. **🚪 Controle de Acesso** - Visitantes e funcionários
4. **🔧 Manutenção & Chamados** - Gestão de manutenção
5. **📦 Portal de Encomendas** - Controle de entregas
6. **🛒 Marketplace** - Classificados
7. **⚠️ Ocorrências** - Registro de incidentes
8. **🔍 Achados e Perdidos** - Itens encontrados
9. **🗳️ Votação** - Assembleias online
10. **📚 Atividades** - Gestão de atividades
11. **💰 Financeiro** - Gestão financeira (futuro)
12. **⚙️ Administração** - Configurações gerais

---

## 2. FLUXO DE AUTENTICAÇÃO E ACESSO

### 2.1 Fluxo de Login

```
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 1: TELA DE LOGIN                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  • Usuário e senha                                      │  │
│  │  • Opção "Lembrar de mim"                               │  │
│  │  • Link "Esqueci minha senha" (futuro)                 │  │
│  │  • Validação de credenciais                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 2: VERIFICAÇÃO                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  • Verificar usuário existe                            │  │
│  │  • Verificar senha correta                             │  │
│  │  • Verificar conta ativa                                │  │
│  │  • Verificar tenant_id (multi-tenancy)                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 3: REDIRECIONAMENTO POR PERFIL                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ADMIN → Dashboard Principal (Módulos)                  │  │
│  │  SALVA-VIDAS → Dashboard Salva-vidas                   │  │
│  │  FUNCIONÁRIO → Dashboard Funcionário                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Tipos de Usuário

| Tipo | Acesso | Dashboard | Módulos Disponíveis |
|------|--------|-----------|---------------------|
| **Admin** | Completo | Dashboard Principal | Todos os módulos |
| **Salva-vidas** | Limitado | Dashboard Salva-vidas | Apenas Piscina |
| **Funcionário** | Médio | Dashboard Funcionário | Acesso, Encomendas, etc |
| **Morador** | Básico | Portal do Morador | Reservas, Classificados, etc |

---

## 3. ESTRUTURA DE NAVEGAÇÃO

### 3.1 Layout Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER (Topo Fixo)                                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ [☰] CondoTech Solutions  [🔍 Busca]  [🔔] [👤 Perfil] [🚪]│ │
│  └───────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐  ┌────────────────────────────────────────────┐  │
│  │          │  │                                             │  │
│  │ SIDEBAR  │  │         CONTEÚDO PRINCIPAL                  │  │
│  │          │  │         (Área de Trabalho)                 │  │
│  │ Módulos  │  │                                             │  │
│  │          │  │  • Cards                                    │  │
│  │ • Piscina│  │  • Tabelas                                   │  │
│  │ • Reserva│  │  • Formulários                              │  │
│  │ • Acesso │  │  • Gráficos                                  │  │
│  │ • ...    │  │  • etc.                                      │  │
│  │          │  │                                             │  │
│  └──────────┘  └────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
│  FOOTER (Rodapé)                                                │
│  © 2024 CondoTech Solutions                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Componentes de Navegação

#### 3.2.1 Header (Topo)
- **Logo/Brand**: CondoTech Solutions
- **Menu Hambúrguer**: Toggle sidebar (mobile)
- **Busca Global**: Pesquisa em todo o sistema
- **Notificações**: Badge com contador
- **Perfil do Usuário**: Dropdown com opções
- **Logout**: Sair do sistema

#### 3.2.2 Sidebar (Lateral)
- **Navegação por Módulos**: Lista de módulos disponíveis
- **Navegação Interna**: Submenu do módulo ativo
- **Estado Colapsado**: Ícones apenas (desktop)
- **Estado Expandido**: Ícones + Texto (desktop/mobile)

#### 3.2.3 Breadcrumbs (Opcional)
- Mostrar localização atual no sistema
- Ex: Home > Piscina > Moradores > Detalhes

---

## 4. MÓDULOS DO SISTEMA

### 4.1 Módulo: Controle de Piscina 🏊

**Acesso**: Admin, Salva-vidas

**Funcionalidades**:
- Dashboard com indicadores em tempo real
- Registro de entrada/saída (QR Code/Manual)
- Cadastro de moradores
- Geração de carteirinhas
- Sistema de alertas de vencimento
- Registro de ocorrências
- Controle de plantão
- Relatórios e gráficos

**Navegação Interna**:
```
Piscina
├── Dashboard
├── Registrar Acesso
│   ├── Entrada
│   └── Saída
├── Moradores
│   ├── Listar
│   ├── Novo
│   └── Detalhes
├── Salva-vidas
│   ├── Listar
│   └── Plantões
├── Ocorrências
│   ├── Listar
│   └── Nova
└── Relatórios
    ├── Histórico de Acessos
    └── Estatísticas
```

### 4.2 Módulo: Reserva de Espaços 📅

**Acesso**: Admin, Moradores

**Funcionalidades**:
- Lista de espaços disponíveis
- Calendário de reservas
- Solicitar reserva
- Aprovar/Rejeitar reservas (admin)
- Lista de convidados
- Histórico de reservas

**Navegação Interna**:
```
Reservas
├── Espaços
│   ├── Listar
│   └── Novo (admin)
├── Calendário
├── Minhas Reservas
├── Solicitar Reserva
└── Aprovações (admin)
```

### 4.3 Módulo: Controle de Acesso 🚪

**Acesso**: Admin, Funcionários

**Funcionalidades**:
- Cadastro de visitantes
- Registro de entrada/saída
- Controle de funcionários
- Controle de prestadores
- Histórico de acessos

**Navegação Interna**:
```
Acesso
├── Visitantes
│   ├── Listar
│   └── Novo
├── Funcionários
├── Prestadores
└── Histórico
```

### 4.4 Módulo: Administração ⚙️

**Acesso**: Apenas Admin

**Funcionalidades**:
- Cadastro de moradores
- Cadastro de funcionários
- Cadastro de salva-vidas
- Configurações do sistema
- Configurações de email
- Gerenciamento de usuários
- Configurações do condomínio

**Navegação Interna**:
```
Administração
├── Dashboard
├── Cadastros
│   ├── Moradores
│   ├── Funcionários
│   └── Salva-vidas
├── Usuários
│   ├── Listar
│   └── Novo
├── Configurações
│   ├── Condomínio
│   ├── Email
│   └── Geral
└── Sistema
    ├── Módulos
    └── Logs
```

---

## 5. HIERARQUIA DE USUÁRIOS E PERMISSÕES

### 5.1 Matriz de Permissões

| Funcionalidade | Admin | Salva-vidas | Funcionário | Morador |
|----------------|-------|-------------|-------------|---------|
| **Piscina** |
| Ver Dashboard | ✅ | ✅ | ❌ | ❌ |
| Registrar Acesso | ✅ | ✅ | ❌ | ❌ |
| Cadastrar Morador | ✅ | ❌ | ❌ | ❌ |
| Gerar Carteirinha | ✅ | ❌ | ❌ | ❌ |
| Registrar Ocorrência | ✅ | ✅ | ❌ | ❌ |
| **Reservas** |
| Ver Espaços | ✅ | ❌ | ❌ | ✅ |
| Solicitar Reserva | ✅ | ❌ | ❌ | ✅ |
| Aprovar Reserva | ✅ | ❌ | ❌ | ❌ |
| **Acesso** |
| Cadastrar Visitante | ✅ | ❌ | ✅ | ❌ |
| Registrar Entrada/Saída | ✅ | ❌ | ✅ | ❌ |
| **Administração** |
| Gerenciar Usuários | ✅ | ❌ | ❌ | ❌ |
| Configurações | ✅ | ❌ | ❌ | ❌ |

### 5.2 Sistema de Permissões Granulares

**Implementação Futura**:
- Permissões por módulo
- Permissões por ação (criar, editar, deletar, visualizar)
- Permissões por tenant (multi-tenancy)
- Grupos de permissões

---

## 6. DESIGN SYSTEM E PADRÕES VISUAIS

### 6.1 Paleta de Cores

#### Cores Principais
- **Primária**: `#007bff` (Azul) - Ações principais, links
- **Secundária**: `#6c757d` (Cinza) - Elementos secundários
- **Sucesso**: `#28a745` (Verde) - Confirmações, sucesso
- **Aviso**: `#ffc107` (Amarelo) - Alertas, atenção
- **Perigo**: `#dc3545` (Vermelho) - Erros, crítico
- **Info**: `#17a2b8` (Ciano) - Informações

#### Cores por Módulo
- **Piscina**: `#007bff` (Azul)
- **Reservas**: `#007bff` (Azul)
- **Acesso**: `#ffc107` (Amarelo)
- **Manutenção**: `#28a745` (Verde)
- **Encomendas**: `#17a2b8` (Ciano)
- **Marketplace**: `#28a745` (Verde)
- **Ocorrências**: `#dc3545` (Vermelho)
- **Achados**: `#ffc107` (Amarelo)
- **Votação**: `#007bff` (Azul)
- **Atividades**: `#17a2b8` (Ciano)

### 6.2 Tipografia

- **Fonte Principal**: System fonts (Arial, Helvetica, sans-serif)
- **Títulos**: Bold, 1.5rem - 2.5rem
- **Subtítulos**: Semi-bold, 1.2rem - 1.5rem
- **Corpo**: Regular, 1rem
- **Pequeno**: Regular, 0.875rem

### 6.3 Componentes Padrão

#### Cards
- Sombra suave
- Border-radius: 8px
- Padding: 1.5rem
- Hover: Elevação + sombra

#### Botões
- Primary: Azul (#007bff)
- Secondary: Cinza (#6c757d)
- Success: Verde (#28a745)
- Danger: Vermelho (#dc3545)
- Tamanhos: sm, md, lg

#### Formulários
- Inputs com borda arredondada
- Labels em negrito
- Mensagens de erro em vermelho
- Ícones de validação

#### Tabelas
- Striped rows
- Hover effect
- Ações em coluna final
- Paginação padrão

### 6.4 Ícones

**Biblioteca**: Font Awesome 6.0

**Padrões**:
- Módulos: Ícones específicos por módulo
- Ações: fas fa-* (solid)
- Status: Ícones coloridos por estado
- Navegação: Ícones consistentes

---

## 7. MELHORIAS E BOAS PRÁTICAS

### 7.1 UX/UI - Melhorias Sugeridas

#### 7.1.1 Navegação
- ✅ **Breadcrumbs**: Adicionar em todas as páginas internas
- ✅ **Atalhos de Teclado**: Implementar atalhos comuns (Ctrl+K para busca)
- ✅ **Busca Global**: Melhorar com sugestões e filtros
- ✅ **Histórico de Navegação**: Botão "Voltar" inteligente

#### 7.1.2 Feedback Visual
- ✅ **Loading States**: Spinners e skeletons durante carregamento
- ✅ **Empty States**: Mensagens quando não há dados
- ✅ **Confirmações**: Modais de confirmação para ações críticas
- ✅ **Toast Notifications**: Notificações não intrusivas

#### 7.1.3 Responsividade
- ✅ **Mobile First**: Design pensado primeiro para mobile
- ✅ **Touch Targets**: Botões com tamanho mínimo de 44x44px
- ✅ **Sidebar Mobile**: Drawer que fecha ao clicar fora
- ✅ **Tabelas Responsivas**: Scroll horizontal ou cards em mobile

### 7.2 Performance

#### 7.2.1 Otimizações
- ✅ **Lazy Loading**: Carregar módulos sob demanda
- ✅ **Paginação**: Limitar resultados por página
- ✅ **Cache**: Cache de dados frequentes
- ✅ **Compressão**: Minificar CSS/JS

#### 7.2.2 Imagens
- ✅ **Lazy Load**: Carregar imagens sob demanda
- ✅ **Otimização**: Comprimir imagens antes do upload
- ✅ **Thumbnails**: Usar thumbnails em listagens
- ✅ **CDN**: Considerar CDN para assets estáticos

### 7.3 Segurança

#### 7.3.1 Autenticação
- ✅ **2FA**: Implementar autenticação de dois fatores (futuro)
- ✅ **Rate Limiting**: Limitar tentativas de login
- ✅ **Session Timeout**: Logout automático após inatividade
- ✅ **Password Policy**: Política de senhas forte

#### 7.3.2 Dados
- ✅ **Validação**: Validar dados no frontend e backend
- ✅ **Sanitização**: Sanitizar inputs do usuário
- ✅ **CSRF Protection**: Proteção contra CSRF
- ✅ **SQL Injection**: Usar ORM (SQLAlchemy já faz isso)

### 7.4 Acessibilidade

#### 7.4.1 WCAG 2.1
- ✅ **Contraste**: Garantir contraste mínimo de 4.5:1
- ✅ **Navegação por Teclado**: Todas as ações acessíveis via teclado
- ✅ **Screen Readers**: Labels e ARIA attributes
- ✅ **Focus Visible**: Indicadores de foco claros

### 7.5 Funcionalidades Futuras

#### 7.5.1 Notificações
- ✅ **Push Notifications**: Notificações do navegador
- ✅ **Email Digest**: Resumo diário/semanal por email
- ✅ **WhatsApp Integration**: Notificações via WhatsApp (já parcialmente implementado)

#### 7.5.2 Relatórios
- ✅ **Exportação**: Exportar dados em CSV/PDF/Excel
- ✅ **Gráficos Interativos**: Gráficos com drill-down
- ✅ **Dashboards Personalizáveis**: Usuário escolhe widgets

#### 7.5.3 Integrações
- ✅ **API REST**: API para integrações externas
- ✅ **Webhooks**: Notificações para sistemas externos
- ✅ **Integração com Portaria**: Integração com sistemas de portaria

### 7.6 Boas Práticas de Código

#### 7.6.1 Estrutura
- ✅ **Separação de Concerns**: Separar lógica, apresentação e dados
- ✅ **Reutilização**: Componentes reutilizáveis
- ✅ **Documentação**: Comentar código complexo
- ✅ **Testes**: Implementar testes unitários e de integração

#### 7.6.2 Manutenibilidade
- ✅ **Versionamento**: Git com commits descritivos
- ✅ **Code Review**: Revisão de código antes de merge
- ✅ **Refatoração**: Refatorar código legado gradualmente
- ✅ **Logging**: Logs estruturados para debugging

---

## 8. ESTRUTURA DE ARQUIVOS RECOMENDADA

```
app/
├── templates/
│   ├── base.html              # Template base
│   ├── base_sidebar.html      # Template com sidebar
│   ├── auth/
│   │   ├── login.html
│   │   └── ...
│   ├── piscina/               # Módulo Piscina
│   │   ├── dashboard.html
│   │   ├── moradores/
│   │   └── ...
│   ├── reservas/              # Módulo Reservas
│   ├── acesso/                # Módulo Acesso
│   └── admin/                 # Módulo Admin
├── static/
│   ├── css/
│   │   ├── style.css          # Estilos globais
│   │   ├── piscina-module.css # Estilos do módulo
│   │   └── ...
│   ├── js/
│   │   ├── main.js            # JS global
│   │   └── ...
│   └── images/
└── ...
```

---

## 9. PRÓXIMOS PASSOS

### Fase 1: Consolidação (Atual)
- ✅ Documentar arquitetura
- ✅ Criar wireframes
- ✅ Definir padrões visuais

### Fase 2: Implementação
- ⏳ Melhorar navegação
- ⏳ Implementar melhorias de UX
- ⏳ Otimizar performance
- ⏳ Adicionar acessibilidade

### Fase 3: Expansão
- ⏳ Novos módulos
- ⏳ Integrações
- ⏳ API REST
- ⏳ Mobile App (futuro)

---

**Versão**: 1.0
**Data**: 2024
**Autor**: Documentação de Arquitetura - CondoTech Solutions

