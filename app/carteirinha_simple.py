"""
Versão simplificada do gerador de carteirinhas
"""

import os
import io
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from flask import current_app
import qrcode

def gerar_qr_code_simples(morador):
    """Gerar QR Code com dados do morador"""
    dados_qr = {
        'id': morador.id,
        'nome': morador.nome_completo,
        'apartamento': f"{morador.bloco}-{morador.apartamento}",
        'validade': morador.data_vencimento.strftime('%d/%m/%Y') if morador.data_vencimento else 'Não definida',
        'status': morador.status_carteirinha,
        'gerada_em': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(dados_qr, ensure_ascii=False))
    qr.make(fit=True)
    
    # Criar imagem do QR code
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para PIL Image padrão
    if hasattr(qr_img, 'convert'):
        return qr_img.convert('RGB')
    else:
        # Se não for PIL Image, salvar e reabrir
        temp_buffer = io.BytesIO()
        qr_img.save(temp_buffer, format='PNG')
        temp_buffer.seek(0)
        return Image.open(temp_buffer).convert('RGB')

def obter_fonte_sistema(tamanho=12, negrito=False):
    """Obter fonte do sistema com fallback"""
    try:
        # Tentar Arial primeiro
        if negrito:
            return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", tamanho)
        else:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", tamanho)
    except:
        try:
            # Fallback para arial básico
            return ImageFont.truetype("arial.ttf", tamanho)
        except:
            # Último recurso - fonte padrão
            return ImageFont.load_default()

def processar_foto_morador(morador, tamanho=(180, 220)):
    """Processar foto do morador ou criar placeholder"""
    foto_path = None
    
    # Tentar encontrar foto anexada
    if hasattr(morador, 'anexos') and morador.anexos.first():
        anexo = morador.anexos.first()
        foto_path = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 
            f'morador_{morador.id}', 
            anexo.nome_arquivo
        )
    
    if foto_path and os.path.exists(foto_path):
        try:
            with Image.open(foto_path) as img:
                # Converter para RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar mantendo proporção
                img.thumbnail(tamanho, Image.Resampling.LANCZOS)
                
                # Criar nova imagem com fundo branco
                nova_img = Image.new('RGB', tamanho, 'white')
                
                # Centralizar
                x = (tamanho[0] - img.width) // 2
                y = (tamanho[1] - img.height) // 2
                nova_img.paste(img, (x, y))
                
                return nova_img
        except Exception as e:
            print(f"Erro ao processar foto: {e}")
    
    # Criar placeholder
    img = Image.new('RGB', tamanho, '#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Desenhar ícone de usuário
    centro_x, centro_y = tamanho[0] // 2, tamanho[1] // 2
    raio = min(tamanho) // 4
    
    # Círculo da cabeça
    draw.ellipse([centro_x - raio//2, centro_y - raio, 
                 centro_x + raio//2, centro_y], fill='#dee2e6')
    
    # Corpo
    draw.ellipse([centro_x - raio, centro_y + raio//2, 
                 centro_x + raio, centro_y + raio*2], fill='#dee2e6')
    
    return img

def gerar_carteirinha_simples(morador, condominio=None):
    """Gerar carteirinha do morador"""
    # Dimensões da carteirinha
    CARD_WIDTH = 1012  # 85.6mm em 300 DPI
    CARD_HEIGHT = 638  # 53.98mm em 300 DPI
    
    # Cores
    COR_PRIMARIA = "#007bff"
    COR_SECUNDARIA = "#6c757d"
    COR_TEXTO = "#2c3e50"
    
    if condominio:
        COR_PRIMARIA = getattr(condominio, 'cor_primaria', COR_PRIMARIA) or COR_PRIMARIA
        COR_SECUNDARIA = getattr(condominio, 'cor_secundaria', COR_SECUNDARIA) or COR_SECUNDARIA
    
    # Criar imagem base
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)
    
    # Fontes
    fonte_titulo = obter_fonte_sistema(24, True)
    fonte_nome = obter_fonte_sistema(20, True)
    fonte_dados = obter_fonte_sistema(14)
    fonte_pequena = obter_fonte_sistema(10)
    
    # === HEADER ===
    header_height = 80
    draw.rectangle([0, 0, CARD_WIDTH, header_height], fill=COR_PRIMARIA)
    
    # Título
    titulo = "CARTEIRINHA DA PISCINA"
    if condominio and hasattr(condominio, 'nome') and condominio.nome:
        titulo = condominio.nome.upper()
    
    # Função para quebrar texto em linhas
    def quebrar_texto_titulo(texto, fonte, largura_max):
        palavras = texto.split()
        linhas = []
        linha_atual = ""
        
        for palavra in palavras:
            teste_linha = linha_atual + (" " if linha_atual else "") + palavra
            try:
                bbox = draw.textbbox((0, 0), teste_linha, font=fonte)
                largura_teste = bbox[2] - bbox[0]
            except:
                largura_teste = len(teste_linha) * 12  # Aproximação
            
            if largura_teste <= largura_max:
                linha_atual = teste_linha
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                    linha_atual = palavra
                else:
                    # Palavra muito longa, quebrar no meio
                    linhas.append(palavra[:len(palavra)//2] + "-")
                    linha_atual = palavra[len(palavra)//2:]
        
        if linha_atual:
            linhas.append(linha_atual)
        
        return linhas
    
    # Quebrar título em linhas se necessário
    largura_max_titulo = CARD_WIDTH - 40  # 20px margem de cada lado
    linhas_titulo = quebrar_texto_titulo(titulo, fonte_titulo, largura_max_titulo)
    
    # Renderizar título linha por linha
    for i, linha in enumerate(linhas_titulo):
        try:
            bbox = draw.textbbox((0, 0), linha, font=fonte_titulo)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(linha) * 12  # Aproximação
        
        x = (CARD_WIDTH - text_width) // 2
        y = 15 + (i * 20)  # 20px entre linhas
        draw.text((x, y), linha, fill='white', font=fonte_titulo)
    
    # === FOTO ===
    foto_size = (180, 220)
    foto_x, foto_y = 50, header_height + 30
    
    foto = processar_foto_morador(morador, foto_size)
    img.paste(foto, (foto_x, foto_y))
    
    # Borda na foto
    draw.rectangle([foto_x-2, foto_y-2, foto_x+foto_size[0]+2, foto_y+foto_size[1]+2], 
                  outline=COR_SECUNDARIA, width=3)
    
    # === DADOS DO MORADOR ===
    dados_x = foto_x + foto_size[0] + 40
    dados_y = header_height + 50
    
    # Nome
    nome = morador.nome_completo.upper()
    if len(nome) > 20:
        palavras = nome.split()
        linha1 = ' '.join(palavras[:len(palavras)//2])
        linha2 = ' '.join(palavras[len(palavras)//2:])
        draw.text((dados_x, dados_y), linha1, fill=COR_TEXTO, font=fonte_nome)
        draw.text((dados_x, dados_y + 25), linha2, fill=COR_TEXTO, font=fonte_nome)
        dados_y += 60
    else:
        draw.text((dados_x, dados_y), nome, fill=COR_TEXTO, font=fonte_nome)
        dados_y += 35
    
    # Apartamento
    apt_text = f"BLOCO {morador.bloco} - APT {morador.apartamento}"
    draw.text((dados_x, dados_y), apt_text, fill=COR_PRIMARIA, font=fonte_dados)
    dados_y += 30
    
    # Validade
    if morador.data_vencimento:
        validade_text = f"VÁLIDA ATÉ: {morador.data_vencimento.strftime('%d/%m/%Y')}"
        cor_validade = '#e74c3c' if morador.status_carteirinha == 'vencida' else '#27ae60'
    else:
        validade_text = "VALIDADE: NÃO DEFINIDA"
        cor_validade = '#f39c12'
    
    draw.text((dados_x, dados_y), validade_text, fill=cor_validade, font=fonte_dados)
    dados_y += 30
    
    # Status
    status_map = {
        'regular': '✓ REGULAR',
        'a_vencer': '⚠ A VENCER',
        'vencida': '✗ VENCIDA',
        'sem_carteirinha': '⚠ SEM CARTEIRINHA'
    }
    status_text = status_map.get(morador.status_carteirinha, '? INDEFINIDO')
    draw.text((dados_x, dados_y), status_text, fill=cor_validade, font=fonte_dados)
    
    # === QR CODE ===
    try:
        qr_img = gerar_qr_code_simples(morador)
        qr_size = 120
        qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_x = CARD_WIDTH - qr_size - 40
        qr_y = header_height + 40
        img.paste(qr_resized, (qr_x, qr_y))
        
        # Label QR Code
        draw.text((qr_x, qr_y + qr_size + 10), "VERIFICAÇÃO", 
                 fill=COR_TEXTO, font=fonte_pequena)
    except Exception as e:
        print(f"Erro ao gerar QR code: {e}")
    
    # === FOOTER ===
    footer_y = CARD_HEIGHT - 60
    draw.rectangle([0, footer_y, CARD_WIDTH, CARD_HEIGHT], fill=COR_SECUNDARIA)
    
    # ID da carteirinha
    id_text = f"ID: {morador.id:04d}"
    draw.text((20, footer_y + 15), id_text, fill='white', font=fonte_pequena)
    
    # Data de emissão
    emissao_text = f"EMITIDA EM: {datetime.now().strftime('%d/%m/%Y')}"
    try:
        bbox = draw.textbbox((0, 0), emissao_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = len(emissao_text) * 8
    
    draw.text((CARD_WIDTH - text_width - 20, footer_y + 15), 
             emissao_text, fill='white', font=fonte_pequena)
    
    return img

def gerar_pdf_carteirinha(morador, condominio=None):
    """Gerar PDF da carteirinha"""
    # Gerar imagem da carteirinha
    img = gerar_carteirinha_simples(morador, condominio)
    
    # Criar PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Salvar imagem temporariamente
    temp_img = io.BytesIO()
    img.save(temp_img, format='PNG')
    temp_img.seek(0)
    
    # Calcular posição centralizada
    card_width_points = 85.6 * mm
    card_height_points = 53.98 * mm
    
    x = (width - card_width_points) / 2
    y = (height - card_height_points) / 2
    
    # Adicionar imagem ao PDF
    c.drawImage(temp_img, x, y, card_width_points, card_height_points)
    
    # Linha de corte
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(0.5)
    c.rect(x, y, card_width_points, card_height_points)
    
    # Texto de instrução
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(x, y - 20, "Corte na linha pontilhada")
    
    c.save()
    buffer.seek(0)
    return buffer

def gerar_lote_pdf(moradores, condominio=None):
    """Gerar PDF com múltiplas carteirinhas"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Dimensões
    card_width_points = 85.6 * mm
    card_height_points = 53.98 * mm
    margin = 20 * mm
    
    # Layout: 2 colunas x 4 linhas
    cards_per_row = 2
    cards_per_col = 4
    cards_per_page = 8
    
    for i, morador in enumerate(moradores):
        # Nova página se necessário
        if i > 0 and i % cards_per_page == 0:
            c.showPage()
        
        # Posição na página
        row = (i % cards_per_page) // cards_per_row
        col = (i % cards_per_page) % cards_per_row
        
        x = margin + col * (card_width_points + 10)
        y = height - margin - (row + 1) * (card_height_points + 10)
        
        # Gerar imagem
        img = gerar_carteirinha_simples(morador, condominio)
        temp_img = io.BytesIO()
        img.save(temp_img, format='PNG')
        temp_img.seek(0)
        
        # Adicionar ao PDF
        c.drawImage(temp_img, x, y, card_width_points, card_height_points)
        
        # Linha de corte
        c.setStrokeColor(HexColor('#cccccc'))
        c.setLineWidth(0.5)
        c.setDash([2, 2])
        c.rect(x, y, card_width_points, card_height_points)
        c.setDash([])
    
    c.save()
    buffer.seek(0)
    return buffer 