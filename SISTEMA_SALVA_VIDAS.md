# 🏊‍♂️ Sistema de Gerenciamento de Salva-vidas

## 📋 Visão Geral

O Sistema de Gerenciamento de Salva-vidas é uma funcionalidade completa integrada ao Sistema de Carteirinhas da Piscina, permitindo o controle total da equipe de salva-vidas do condomínio.

## ⭐ Funcionalidades Principais

### 👥 Gestão da Equipe
- **Cadastro completo** de salva-vidas com dados pessoais e profissionais
- **Controle de status** (Ativo, Inativo, Demitido, Férias, Licença)
- **Upload de fotos** para identificação visual
- **Histórico profissional** com datas de contratação e demissão

### 📜 Certificações e Qualificações
- **Certificação em Salvamento Aquático**
- **Certificação em Primeiros Socorros**
- **Controle de vencimento** das certificações
- **Outras qualificações** (texto livre para especialidades)

### 💰 Dados Profissionais
- **Salário** (campo opcional)
- **Horários de trabalho** detalhados
- **Tempo de serviço** calculado automaticamente
- **Observações** para anotações importantes

### 📊 Relatórios e Estatísticas
- **Dashboard integrado** com estatísticas da equipe
- **Filtros avançados** por status, certificações e nome
- **Contadores automáticos** de ativos, inativos e certificados
- **Percentuais calculados** automaticamente

## 🚀 Como Usar

### 1. Acessando o Sistema
- Acesse o menu **"Salva-vidas"** na barra de navegação
- Opções disponíveis:
  - **Listar Equipe**: Ver todos os salva-vidas cadastrados
  - **Novo Salva-vidas**: Cadastrar novo membro da equipe

### 2. Cadastrando um Salva-vidas

#### Dados Pessoais (Obrigatórios)
- **Nome Completo**
- **CPF** (único no sistema)
- **Data de Nascimento**
- **Telefone**

#### Dados Pessoais (Opcionais)
- **RG**
- **Email**
- **Endereço completo**

#### Dados Profissionais
- **Data de Contratação** (obrigatória)
- **Status** (padrão: Ativo)
- **Data de Demissão** (apenas se aplicável)
- **Salário** (opcional, campo privado)
- **Horário de Trabalho** (descrição dos turnos)

#### Certificações
- ☑️ **Certificação em Salvamento Aquático**
- ☑️ **Certificação em Primeiros Socorros**
- **Data de Vencimento** das certificações
- **Outras Qualificações** (texto livre)

#### Observações
- Campo livre para anotações importantes
- Histórico de mudanças
- Notas sobre desempenho

### 3. Gerenciando a Equipe

#### Visualização
- **Lista completa** com fotos, status e certificações
- **Página de detalhes** individual com todas as informações
- **Filtros** por status, certificações e busca por nome

#### Ações Rápidas
- **Inativar/Reativar** salva-vidas
- **Editar dados** pessoais e profissionais
- **Visualizar histórico** completo

### 4. Dashboard e Relatórios

#### Estatísticas Principais
- **Total da Equipe**: Número total de salva-vidas
- **Ativos**: Quantos estão trabalhando
- **Certificados**: Quantos têm ambas as certificações

#### Filtros Disponíveis
- **Por Status**: Ativo, Inativo, Demitido, Férias, Licença
- **Por Certificação**: Salvamento, Primeiros Socorros, Ambas
- **Por Nome**: Busca textual

## 📱 Interface

### 🎨 Design Responsivo
- Interface moderna com **Bootstrap 5**
- **Ícones Font Awesome** para melhor UX
- **Cards informativos** com cores por status
- **Badges** para certificações e status

### 📊 Indicadores Visuais
- **Verde**: Ativo, Certificado, Válido
- **Amarelo**: Férias, Atenção
- **Vermelho**: Demitido, Vencido
- **Azul**: Informações gerais
- **Cinza**: Inativo, Não informado

## 🔧 Configurações Técnicas

### 📁 Estrutura de Arquivos
```
app/
├── models.py              # Modelo SalvaVidas
├── forms.py               # Formulários (SalvaVidasForm, FiltroSalvaVidasForm)
├── routes.py              # Rotas para CRUD
├── static/uploads/salva_vidas/  # Fotos dos salva-vidas
└── templates/salva_vidas/
    ├── listar.html        # Lista com filtros
    ├── form.html          # Cadastro/Edição
    └── detalhes.html      # Visualização completa
```

### 🗄️ Banco de Dados
A tabela `salva_vidas` contém:
- **Dados pessoais**: nome, cpf, rg, nascimento, contatos
- **Dados profissionais**: contratação, demissão, status, salário
- **Certificações**: salvamento, primeiros socorros, vencimento
- **Controle**: observações, foto, timestamps
- **Relacionamentos**: condomínio_id (FK)

### 🔐 Campos Únicos
- **CPF**: Não permite duplicatas
- **ID**: Chave primária auto-incremento

## 📈 Campos Calculados

### Propriedades Automáticas
- **`idade`**: Calculada a partir da data de nascimento
- **`tempo_servico`**: Anos de trabalho (considerando demissão se aplicável)
- **`certificacao_valida`**: Verifica se certificações estão no prazo
- **`status_badge_class`**: Classe CSS para badges coloridos

## 🔍 Validações

### Campos Obrigatórios
- Nome completo (2-200 caracteres)
- CPF (11-14 caracteres, único)
- Data de nascimento
- Telefone (10-20 caracteres)
- Data de contratação
- Status (seleção obrigatória)

### Campos Opcionais
- RG, Email, Endereço
- Data de demissão
- Salário (números positivos)
- Certificações (checkboxes)
- Data de vencimento das certificações
- Outras qualificações, Horário, Observações

### Upload de Fotos
- **Formatos aceitos**: JPG, JPEG, PNG, GIF
- **Tamanho máximo**: 16MB
- **Armazenamento**: `/app/static/uploads/salva_vidas/`
- **Nomenclatura**: `salva_vidas_{id}_{hash}.{ext}`

## 🚦 Status Disponíveis

| Status | Descrição | Cor |
|--------|-----------|-----|
| **Ativo** | Trabalhando normalmente | 🟢 Verde |
| **Inativo** | Temporariamente afastado | ⚫ Cinza |
| **Demitido** | Não trabalha mais | 🔴 Vermelho |
| **Férias** | Em período de férias | 🟡 Amarelo |
| **Licença** | Licença médica/pessoal | 🔵 Azul |

## 🎯 Integração com Dashboard

### Estatísticas no Dashboard Principal
- **Total da Equipe**: Link direto para listagem
- **Salva-vidas Ativos**: Com percentual da equipe
- **Certificados**: Ambas as certificações válidas

### Ações Rápidas
- **Novo Salva-vidas**: Botão direto no dashboard
- **Ver Equipe**: Acesso rápido à listagem

## 📝 Exemplo de Uso

### Cenário Típico
1. **Contratação**: Cadastrar novo salva-vidas com dados completos
2. **Certificação**: Marcar certificações obtidas e prazo
3. **Acompanhamento**: Verificar periodicamente vencimentos
4. **Gestão**: Inativar temporariamente por férias/licença
5. **Histórico**: Registrar observações sobre desempenho

### Relatórios Úteis
- **Certificações vencendo**: Filtrar por data de vencimento
- **Equipe ativa**: Apenas status "Ativo"
- **Histórico completo**: Incluindo ex-funcionários

## 🔄 Atualizações Futuras

### Possíveis Melhorias
- **Notificações automáticas** para vencimento de certificações
- **Relatórios em PDF** da equipe
- **Controle de escalas** e horários
- **Integração com folha de pagamento**
- **QR Code** para identificação rápida
- **App mobile** para gestão em campo

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se todos os campos obrigatórios estão preenchidos
2. Confirme que o CPF não está duplicado
3. Certifique-se que a foto está no formato correto
4. Consulte os logs do sistema em **Configurações → Ver Logs**

---

**Sistema desenvolvido com Flask, SQLAlchemy e Bootstrap 5** 🚀 