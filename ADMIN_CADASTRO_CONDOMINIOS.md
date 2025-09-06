# 🏢 Sistema de Cadastro de Condomínios - Painel Admin

## 🎯 **Visão Geral**

Sistema completo e intuitivo para cadastro e gestão de novos condomínios no painel administrativo do CondoTech Solutions. Permite criar novos tenants de forma rápida e profissional.

---

## 🚀 **Funcionalidades Implementadas**

### **✅ Cadastro de Novos Condomínios**
- **Formulário intuitivo** com validação em tempo real
- **Preview dinâmico** das informações inseridas
- **Verificação automática** de disponibilidade de subdomínio
- **Sugestões inteligentes** de subdomínio baseadas no nome
- **Validação completa** de dados (email, CNPJ, etc.)
- **Configuração inicial** automática do tenant

### **✅ Interface Moderna**
- **Design responsivo** para desktop e mobile
- **Validação em tempo real** via AJAX
- **Máscaras automáticas** para CNPJ e telefone
- **Feedback visual** instantâneo
- **Preview card** com informações atualizadas

### **✅ Gestão de Condomínios**
- **Listagem completa** com filtros
- **Edição de dados** do condomínio
- **Controle de status** (ativo, suspenso, cancelado)
- **Gestão de planos** e módulos
- **Estatísticas** em tempo real

---

## 📋 **Arquivos Criados/Modificados**

### **Novos Arquivos**
```
app/forms_admin.py                    # Formulários para administração
app/templates/admin/novo_condominio.html     # Template de cadastro
app/templates/admin/editar_condominio.html   # Template de edição
inicializar_dados_admin.py            # Script de inicialização
ADMIN_CADASTRO_CONDOMINIOS.md         # Esta documentação
```

### **Arquivos Modificados**
```
app/admin_routes.py                   # Novas rotas administrativas
app/templates/admin/tenants.html      # Melhorias na listagem
```

---

## 🛠️ **Como Usar**

### **1. Inicialização (Primeira Vez)**
```bash
# Instalar dependências se necessário
pip install -r requirements.txt

# Inicializar dados básicos (planos e módulos)
python inicializar_dados_admin.py

# Criar usuário administrador (se não existir)
python criar_admin.py
```

### **2. Acessar o Sistema**
1. **Login** como administrador
2. **Navegar** para `/admin/tenants`
3. **Clicar** em "Novo Condomínio"
4. **Preencher** o formulário
5. **Salvar** e pronto!

---

## 📝 **Fluxo de Cadastro**

### **Passo 1: Dados Básicos**
```
Nome do Condomínio: [Residencial Jardim das Flores]
Subdomínio: [jardimflores] ✅ Disponível
Plano: [Profissional - R$ 149/mês]
```

### **Passo 2: Responsável**
```
Nome: [João Silva]
Email: [joao@residencialjardim.com.br]
Senha: [●●●●●●●●]
Telefone: [(11) 99999-9999]
CNPJ: [12.345.678/0001-90] (opcional)
```

### **Passo 3: Configurações**
```
☑️ Criar dados de exemplo
☑️ Enviar email de boas-vindas
```

### **Resultado**
```
✅ Condomínio "Residencial Jardim das Flores" criado!
🔑 Login: joao@residencialjardim.com.br
🌐 Acesso: https://jardimflores.condotech.com.br
📧 Email de boas-vindas enviado!
```

---

## 🔧 **Validações Implementadas**

### **Subdomínio**
- ✅ Apenas letras minúsculas e números
- ✅ Mínimo 3 caracteres
- ✅ Não pode ser reservado (www, api, admin, etc.)
- ✅ Verificação de disponibilidade em tempo real
- ✅ Sugestões automáticas se não disponível

### **Email**
- ✅ Formato válido
- ✅ Não pode estar em uso por outro admin
- ✅ Será usado como login

### **CNPJ (Opcional)**
- ✅ Formato válido (14 dígitos)
- ✅ Máscara automática
- ✅ Não pode estar duplicado

### **Senha**
- ✅ Mínimo 6 caracteres
- ✅ Confirmação obrigatória
- ✅ Botão mostrar/ocultar

---

## 🎨 **Interface e UX**

### **Design Responsivo**
- **Desktop**: Layout em 2 colunas com preview
- **Mobile**: Layout em 1 coluna adaptável
- **Tablet**: Interface otimizada para touch

### **Validação em Tempo Real**
```javascript
// Verificação de subdomínio
inputSubdominio.addEventListener('input', function() {
    // Debounce 500ms
    // Verificação via AJAX
    // Feedback visual instantâneo
    // Sugestões automáticas
});
```

### **Preview Dinâmico**
```javascript
// Atualização em tempo real
function atualizarPreview() {
    previewNome.textContent = inputNome.value || 'Nome do Condomínio';
    previewUrl.innerHTML = inputSubdominio.value + '.condotech.com.br';
    // ... outros campos
}
```

---

## 🔌 **APIs Implementadas**

### **Verificar Subdomínio**
```
GET /admin/api/verificar-subdominio?subdominio=exemplo

Response:
{
    "disponivel": false,
    "mensagem": "Subdomínio já está em uso",
    "sugestoes": ["exemplo1", "exemplo2", "exemploapp"]
}
```

### **Sugerir Subdomínio**
```
GET /admin/api/sugerir-subdominio?nome=Residencial Jardim das Flores

Response:
{
    "sugestoes": ["residencialjardim", "rjf", "jardimflores"]
}
```

---

## 📊 **Dados Criados Automaticamente**

### **Tenant (Condomínio)**
```python
tenant = Tenant(
    nome=dados['nome'],
    subdominio=dados['subdominio'],
    email_responsavel=dados['email'],
    plano_id=dados['plano_id'],
    data_inicio=hoje,
    data_vencimento=hoje + 30_dias,  # 30 dias grátis
    status='ativo'
)
```

### **Usuário Administrador**
```python
admin = Usuario(
    username=dados['email'],
    email=dados['email'],
    nome_completo=dados['nome_responsavel'],
    tipo_usuario='admin',
    tenant_id=tenant.id,
    permissoes={
        'admin_tenant': True,
        'criar_morador': True,
        'validar_carteirinha': True,
        # ... todas as permissões
    }
)
```

### **Configurações Iniciais**
```python
configuracoes = [
    ('email', 'servidor_smtp', 'smtp.gmail.com'),
    ('carteirinhas', 'validade_padrao_meses', '12'),
    ('sistema', 'nome_sistema', 'Sistema de Carteirinhas'),
    # ... outras configurações
]
```

### **Dados de Exemplo (Opcional)**
```python
moradores_exemplo = [
    {'nome': 'João Silva', 'bloco': 'A', 'apartamento': '101'},
    {'nome': 'Maria Santos', 'bloco': 'B', 'apartamento': '205'},
    {'nome': 'Pedro Silva', 'bloco': 'A', 'apartamento': '101', 'eh_titular': False}
]
```

---

## 🔐 **Segurança**

### **Validações Backend**
- ✅ **CSRF Protection** em todos os formulários
- ✅ **Sanitização** de dados de entrada
- ✅ **Validação** de tipos e formatos
- ✅ **Verificação** de duplicatas

### **Controle de Acesso**
- ✅ **Login obrigatório** para todas as rotas admin
- ✅ **Verificação** de permissões de administrador
- ✅ **Isolamento** de dados por tenant

### **Validação de Dados**
```python
def validate_subdominio(self, field):
    subdominio = field.data.lower().strip()
    
    # Verificar caracteres permitidos
    if not re.match(r'^[a-z0-9]+$', subdominio):
        raise ValidationError('Apenas letras e números')
    
    # Verificar se não é reservado
    if subdominio in ['www', 'api', 'admin']:
        raise ValidationError('Subdomínio reservado')
    
    # Verificar se já existe
    if Tenant.query.filter_by(subdominio=subdominio).first():
        raise ValidationError('Subdomínio já em uso')
```

---

## 🎯 **Próximos Passos**

### **Melhorias Planejadas**
- [ ] **Wizard multi-etapas** para cadastro
- [ ] **Upload de logo** do condomínio
- [ ] **Configuração de cores** personalizadas
- [ ] **Importação em lote** de moradores
- [ ] **Templates de email** personalizáveis
- [ ] **Dashboard de onboarding** com progresso

### **Integrações Futuras**
- [ ] **Gateway de pagamento** para cobrança automática
- [ ] **API de CEP** para preenchimento automático
- [ ] **Validação real de CNPJ** via Receita Federal
- [ ] **Envio de SMS** além de email
- [ ] **Notificações push** para admins

---

## 🐛 **Solução de Problemas**

### **Erro: Subdomínio não disponível**
```
Causa: Subdomínio já está em uso
Solução: Use as sugestões automáticas ou escolha outro nome
```

### **Erro: Email já cadastrado**
```
Causa: Email já é admin de outro condomínio
Solução: Use um email diferente ou verifique duplicatas
```

### **Erro: Planos não encontrados**
```
Causa: Dados básicos não foram inicializados
Solução: Execute python inicializar_dados_admin.py
```

### **Erro: Permissão negada**
```
Causa: Usuário não é administrador
Solução: Faça login com conta de administrador
```

---

## 📞 **Suporte**

### **Para Desenvolvedores**
- **Documentação**: Este arquivo
- **Código**: Comentado e organizado
- **Logs**: Sistema de logging integrado
- **Debug**: Mode debug disponível

### **Para Usuários**
- **Interface intuitiva** com tooltips
- **Validação em tempo real** com feedback
- **Mensagens de erro** claras e acionáveis
- **Sugestões automáticas** para resolução

---

**🏆 Sistema pronto para produção com interface profissional e validações completas!**
