"""
Serviço para geração de carteirinhas
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
        'status': morador.status_carteirinha,
        'gerada_em': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    try:
        # Configurar QR Code com parâmetros otimizados
        qr = qrcode.QRCode(
            version=2,  # Versão maior para mais dados
            error_correction=qrcode.ERROR_CORRECT_M,
            box_size=8,  # Tamanho menor dos quadrados
            border=2,    # Borda menor
        )
        
        # Adicionar dados como string simples
        dados_string = f"ID:{morador.id}|NOME:{morador.nome_completo}|APT:{morador.bloco}-{morador.apartamento}|STATUS:{morador.status_carteirinha}"
        qr.add_data(dados_string)
        qr.make(fit=True)
        
        # Criar imagem do QR code
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar em buffer e reabrir como PIL Image
        buffer = io.BytesIO()
        qr_img.save(buffer, 'PNG')
        buffer.seek(0)
        
        # Carregar como PIL Image RGB
        pil_img = Image.open(buffer)
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Redimensionar para tamanho padrão
        qr_final = pil_img.resize((200, 200), Image.Resampling.LANCZOS)
        
        return qr_final
        
    except Exception as e:
        print(f"Erro ao gerar QR code: {e}")
        # Fallback: criar QR code visual simples
        fallback_img = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(fallback_img)
        
        # Desenhar padrão de QR code simples
        cell_size = 8
        for i in range(0, 200, cell_size):
            for j in range(0, 200, cell_size):
                # Criar padrão pseudo-aleatório baseado na posição
                if (i + j) % 16 == 0 or (i * j) % 24 == 0:
                    draw.rectangle([i, j, i + cell_size, j + cell_size], fill='black')
        
        # Adicionar cantos de referência do QR code
        corner_size = 40
        # Canto superior esquerdo
        draw.rectangle([10, 10, 10 + corner_size, 10 + corner_size], outline='black', width=3)
        draw.rectangle([20, 20, 20 + corner_size - 20, 20 + corner_size - 20], fill='black')
        
        # Canto superior direito
        draw.rectangle([200 - 10 - corner_size, 10, 200 - 10, 10 + corner_size], outline='black', width=3)
        draw.rectangle([200 - 30, 20, 200 - 20, 30], fill='black')
        
        # Canto inferior esquerdo
        draw.rectangle([10, 200 - 10 - corner_size, 10 + corner_size, 200 - 10], outline='black', width=3)
        draw.rectangle([20, 200 - 30, 30, 200 - 20], fill='black')
        
        return fallback_img

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
    
    # Buscar especificamente a foto da carteirinha
    if hasattr(morador, 'foto_carteirinha') and morador.foto_carteirinha:
        foto_carteirinha = morador.foto_carteirinha
        foto_path = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), 
            f'morador_{morador.id}', 
            foto_carteirinha.nome_arquivo
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
    
    # Criar placeholder se não houver foto
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

def gerar_carteirinha_completa(morador, condominio=None):
    """Gerar carteirinha com design simples e limpo baseado na imagem de referência"""
    # Dimensões da carteirinha
    CARD_WIDTH = 1012  # 85.6mm em 300 DPI
    CARD_HEIGHT = 638  # 53.98mm em 300 DPI
    
    # Cores
    if condominio:
        cor_primaria = getattr(condominio, 'cor_primaria', "#1e3a8a") or "#1e3a8a"
        cor_secundaria = getattr(condominio, 'cor_secundaria', "#3b82f6") or "#3b82f6"
    else:
        cor_primaria = "#1e3a8a"  # Azul escuro
        cor_secundaria = "#3b82f6"  # Azul médio
    
    # Criar imagem base
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), '#ffffff')
    draw = ImageDraw.Draw(img)
    
    # Fontes
    fonte_titulo = obter_fonte_sistema(24, True)
    fonte_subtitulo = obter_fonte_sistema(16, True)
    fonte_nome = obter_fonte_sistema(20, True)
    fonte_dados = obter_fonte_sistema(14)
    fonte_pequena = obter_fonte_sistema(12)
    
    # === HEADER AZUL SUPERIOR ===
    header_height = 120
    
    # Fundo azul sólido no header
    draw.rectangle([0, 0, CARD_WIDTH, header_height], fill=cor_primaria)
    
    # === LOGO/ÍCONE NO HEADER ===
    logo_x, logo_y = 30, 25
    logo_size = 70
    
    # Círculo branco para o logo
    draw.ellipse([logo_x, logo_y, logo_x + logo_size, logo_y + logo_size], 
                fill='white', outline='white', width=2)
    
    # Ícone de piscina no centro do círculo
    center_x, center_y = logo_x + logo_size//2, logo_y + logo_size//2
    
    # Desenhar ondas estilizadas (representando piscina)
    for i in range(3):
        wave_y = center_y - 15 + (i * 10)
        draw.ellipse([center_x - 25, wave_y, center_x + 25, wave_y + 6], 
                    fill=cor_primaria, outline=cor_primaria)
    
    # === TÍTULO DO CONDOMÍNIO ===
    if condominio and hasattr(condominio, 'nome') and condominio.nome:
        titulo = condominio.nome.upper()
    else:
        titulo = "CONDOMÍNIO"
    
    # Posicionar título ao lado do logo
    titulo_x = logo_x + logo_size + 20
    titulo_y = logo_y + 5
    
    # Quebrar título em linhas se necessário
    palavras = titulo.split()
    linhas = []
    linha_atual = ""
    
    for palavra in palavras:
        teste_linha = linha_atual + (" " if linha_atual else "") + palavra
        try:
            bbox = draw.textbbox((0, 0), teste_linha, font=fonte_titulo)
            largura_teste = bbox[2] - bbox[0]
        except:
            largura_teste = len(teste_linha) * 12
        
        if largura_teste <= (CARD_WIDTH - titulo_x - 20):
            linha_atual = teste_linha
        else:
            if linha_atual:
                linhas.append(linha_atual)
                linha_atual = palavra
            else:
                linhas.append(palavra)
    
    if linha_atual:
        linhas.append(linha_atual)
    
    # Renderizar título
    for i, linha in enumerate(linhas):
        draw.text((titulo_x, titulo_y + (i * 28)), linha, fill='white', font=fonte_titulo)
    
    # === SUBTÍTULO ===
    subtitulo_y = titulo_y + (len(linhas) * 28) + 5
    draw.text((titulo_x, subtitulo_y), "CARTEIRINHA DA PISCINA", fill='white', font=fonte_subtitulo)
    
    # === ÁREA PRINCIPAL ===
    main_y = header_height + 30
    
    # === FOTO DO MORADOR ===
    foto_size = (140, 170)
    foto_x, foto_y = 40, main_y
    
    foto = processar_foto_morador(morador, foto_size)
    
    # Moldura simples da foto
    draw.rectangle([foto_x - 3, foto_y - 3, 
                   foto_x + foto_size[0] + 3, foto_y + foto_size[1] + 3], 
                  fill='white', outline='#cccccc', width=2)
    
    img.paste(foto, (foto_x, foto_y))
    
    # === INFORMAÇÕES DO MORADOR ===
    info_x = foto_x + foto_size[0] + 30
    info_y = main_y
    
    # Nome do morador
    nome = morador.nome_completo.upper()
    draw.text((info_x, info_y), "NOME:", fill='#333333', font=fonte_dados)
    
    # Quebrar nome em linhas se necessário
    nome_y = info_y + 20
    if len(nome) > 25:
        palavras = nome.split()
        meio = len(palavras) // 2
        linha1 = ' '.join(palavras[:meio])
        linha2 = ' '.join(palavras[meio:])
        
        draw.text((info_x, nome_y), linha1, fill='black', font=fonte_nome)
        draw.text((info_x, nome_y + 25), linha2, fill='black', font=fonte_nome)
        info_y = nome_y + 55
    else:
        draw.text((info_x, nome_y), nome, fill='black', font=fonte_nome)
        info_y = nome_y + 35
    
    # Email
    draw.text((info_x, info_y), "EMAIL:", fill='#333333', font=fonte_dados)
    draw.text((info_x, info_y + 18), morador.email, fill='black', font=fonte_dados)
    info_y += 45
    
    # Celular
    draw.text((info_x, info_y), "CELULAR:", fill='#333333', font=fonte_dados)
    draw.text((info_x, info_y + 18), morador.celular, fill='black', font=fonte_dados)
    info_y += 45
    
    # Bloco e Apartamento
    draw.text((info_x, info_y), "BLOCO/APARTAMENTO:", fill='#333333', font=fonte_dados)
    bloco_apto = f"BLOCO {morador.bloco} - APTO {morador.apartamento}"
    draw.text((info_x, info_y + 18), bloco_apto, fill='black', font=fonte_dados)
    info_y += 45
    
    # Tipo (Titular ou Dependente)
    draw.text((info_x, info_y), "TIPO:", fill='#333333', font=fonte_dados)
    tipo = "TITULAR" if morador.eh_titular else "DEPENDENTE"
    draw.text((info_x, info_y + 18), tipo, fill='black', font=fonte_dados)
    
    # === QR CODE ===
    try:
        qr_img = gerar_qr_code_simples(morador)
        qr_size = 120
        qr_x = CARD_WIDTH - qr_size - 40
        qr_y = main_y + 20
        
        # Moldura do QR Code
        draw.rectangle([qr_x - 5, qr_y - 5, qr_x + qr_size + 5, qr_y + qr_size + 5], 
                      fill='white', outline='#cccccc', width=2)
        
        # Redimensionar e colar QR Code
        qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        img.paste(qr_resized, (qr_x, qr_y))
        
        # Label do QR Code
        qr_label = "CÓDIGO DE VERIFICAÇÃO"
        try:
            bbox = draw.textbbox((0, 0), qr_label, font=fonte_pequena)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(qr_label) * 8
        
        label_x = qr_x + (qr_size - text_width) // 2
        label_y = qr_y + qr_size + 10
        draw.text((label_x, label_y), qr_label, fill='#666666', font=fonte_pequena)
        
    except Exception as e:
        print(f"Erro ao gerar QR code: {e}")
    
    # === FOOTER ===
    footer_height = 50
    footer_y = CARD_HEIGHT - footer_height
    
    # Linha separadora
    draw.line([(20, footer_y), (CARD_WIDTH - 20, footer_y)], fill='#cccccc', width=2)
    
    # ID da carteirinha
    id_text = f"ID: {morador.id:05d}"
    draw.text((30, footer_y + 15), id_text, fill='#666666', font=fonte_pequena)
    
    # Data de emissão centralizada
    emissao_text = f"Emitida em {datetime.now().strftime('%d/%m/%Y')}"
    try:
        bbox = draw.textbbox((0, 0), emissao_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = len(emissao_text) * 8
    
    center_x = (CARD_WIDTH - text_width) // 2
    draw.text((center_x, footer_y + 15), emissao_text, fill='#666666', font=fonte_pequena)
    
    # Texto "DOCUMENTO OFICIAL"
    oficial_text = "DOCUMENTO OFICIAL"
    try:
        bbox = draw.textbbox((0, 0), oficial_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = len(oficial_text) * 8
    
    draw.text((CARD_WIDTH - text_width - 30, footer_y + 15), oficial_text, fill='#666666', font=fonte_pequena)
    
    # === BORDA FINAL ===
    draw.rectangle([0, 0, CARD_WIDTH-1, CARD_HEIGHT-1], 
                  outline='#cccccc', width=2)
    
    return img

def gerar_pdf_carteirinha(morador, condominio=None):
    """Gerar PDF da carteirinha"""
    # Gerar imagem da carteirinha
    img = gerar_carteirinha_completa(morador, condominio)
    
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
    
    # Adicionar imagem ao PDF usando ImageReader
    from reportlab.lib.utils import ImageReader
    img_reader = ImageReader(temp_img)
    c.drawImage(img_reader, x, y, card_width_points, card_height_points)
    
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
        img = gerar_carteirinha_completa(morador, condominio)
        temp_img = io.BytesIO()
        img.save(temp_img, format='PNG')
        temp_img.seek(0)
        
        # Adicionar ao PDF usando ImageReader
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(temp_img)
        c.drawImage(img_reader, x, y, card_width_points, card_height_points)
        
        # Linha de corte
        c.setStrokeColor(HexColor('#cccccc'))
        c.setLineWidth(0.5)
        c.setDash([2, 2])
        c.rect(x, y, card_width_points, card_height_points)
        c.setDash([])
    
    c.save()
    buffer.seek(0)
    return buffer 