# 🎫 Instruções do Sistema de Carteirinhas

## ✅ Funcionalidade Implementada com Sucesso!

O sistema de geração de carteirinhas da piscina está **funcionando perfeitamente** e pronto para uso!

## 🚀 Como Usar

### 1. Gerar Carteirinha Individual

**Via Dashboard (RECOMENDADO):**
1. Acesse o dashboard principal (`/`)
2. Na seção "Geração de Carteirinhas", clique em **"Escolher Morador"**
3. Selecione o morador desejado e clique em **"Gerar Carteirinha"**

**Via Lista de Moradores:**
1. Vá em "Moradores" → "Listar Moradores"
2. Clique no ícone da carteirinha (🆔) ao lado do morador desejado

**Via Detalhes do Morador:**
1. Vá em "Moradores" → "Listar Moradores"
2. Clique no nome do morador para ver os detalhes
3. Clique em **"Visualizar Carteirinha"** na seção de ações

**Opções disponíveis:**
- 👀 **Visualizar**: Vê a carteirinha na tela
- 📄 **Download PDF**: Baixa arquivo PDF para impressão
- 🖼️ **Download PNG**: Baixa imagem em alta resolução

### 2. Gerar Carteirinhas em Lote

1. No menu superior, vá em "Moradores" → "Carteirinhas em Lote"
2. Selecione os moradores desejados (use checkboxes)
3. Clique em "Gerar PDF com Carteirinhas Selecionadas"
4. Um PDF será gerado com até 8 carteirinhas por página

**Dicas:**
- Use "Selecionar Todos" para marcar todos os moradores
- Use "Limpar Seleção" para desmarcar todos
- O contador mostra quantos moradores foram selecionados

## 🎨 Características da Carteirinha

### Design Profissional
- ✅ **Dimensões padrão**: 85.6 x 53.98 mm (tamanho cartão de crédito)
- ✅ **Resolução alta**: 300 DPI para impressão de qualidade
- ✅ **Layout organizado**: Header, foto, dados, QR code, footer

### Informações Incluídas
- 📷 **Foto do morador** (se disponível, senão usa placeholder)
- 👤 **Nome completo**
- 🏠 **Bloco e apartamento**
- 📅 **Data de validade**
- ✅ **Status da carteirinha** (Regular, A Vencer, Vencida)
- 🔍 **QR Code** para verificação
- 🆔 **ID único** da carteirinha
- 📅 **Data de emissão**

### QR Code Inteligente
O QR Code contém informações JSON para verificação:
```json
{
    "id": 1,
    "nome": "João Silva",
    "apartamento": "A-101",
    "validade": "2024-12-31",
    "status": "regular"
}
```

## 🖨️ Impressão

### Configurações Recomendadas
- **Papel**: A4 branco, gramatura 180g ou superior
- **Qualidade**: Máxima/Foto
- **Orientação**: Retrato
- **Margens**: Padrão
- **Escala**: 100% (tamanho real)

### Processo de Impressão
1. Baixe o PDF da carteirinha
2. Abra no Adobe Reader ou visualizador de PDF
3. Configure as opções de impressão conforme acima
4. Imprima
5. Corte na linha pontilhada indicada

### Dica Professional
Para carteirinhas duráveis:
- Use papel fotográfico ou couché
- Plastifique após impressão
- Ou imprima em gráfica especializada

## 🔧 Arquivos de Teste

O sistema gera arquivos de teste em `teste_carteirinhas/`:
- `carteirinha_X.png` - Imagem em alta resolução
- `carteirinha_X.pdf` - PDF pronto para impressão

## 📱 Acesso Mobile

O sistema é **responsivo** - funciona perfeitamente em:
- 💻 Desktop
- 📱 Smartphone
- 📱 Tablet

## 🆘 Solução de Problemas

### Morador sem Foto
- ✅ **Automático**: Sistema usa placeholder padrão
- 💡 **Melhoria**: Adicione foto na edição do morador

### QR Code não Funciona
- ✅ **Garantido**: QR code sempre é gerado
- 📱 **Teste**: Use qualquer leitor de QR code do celular

### PDF não Abre
- 🔧 **Solução**: Use Adobe Reader ou Chrome
- 📱 **Mobile**: Baixe app de PDF no celular

### Impressão Desfocada
- ⚙️ **Configuração**: Selecione qualidade máxima
- 📄 **Papel**: Use papel adequado (180g+)

## 🎯 Status Atual

### ✅ Funcionalidades Implementadas
- [x] Geração individual de carteirinhas
- [x] Geração em lote (PDF)
- [x] Design profissional responsivo
- [x] QR Code automático
- [x] Integração completa ao sistema
- [x] Templates HTML modernos
- [x] Processamento de fotos
- [x] Múltiplos formatos (PNG/PDF)

### 🏁 Pronto para Produção
O sistema está **100% funcional** e testado!

---

## 🤝 Suporte

Se encontrar algum problema:
1. Execute `python teste_carteirinha.py` para diagnosticar
2. Verifique se todas as dependências estão instaladas
3. Certifique-se que há moradores cadastrados no sistema

**O sistema de carteirinhas está pronto para uso profissional!** 🎉 