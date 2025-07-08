"""
Serviço para geração de carteirinhas da piscina
"""

import os
import io
import json
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from flask import current_app

class CarteirinhaGenerator:
    def __init__(self):
        # Dimensões da carteirinha (padrão cartão de crédito em pixels - 300 DPI)
        self.CARD_WIDTH = 1012  # 85.6mm * 300 DPI / 25.4
        self.CARD_HEIGHT = 638  # 53.98mm * 300 DPI / 25.4
        
        # Cores padrão
        self.COR_PRIMARIA = "#007bff"
        self.COR_SECUNDARIA = "#6c757d"
        self.COR_FUNDO = "#ffffff"
        self.COR_TEXTO = "#2c3e50"
    
    def _get_font(self, size, bold=False):
        """Obter fonte com fallback para fontes do sistema"""
        try:
            if bold:
                return ImageFont.truetype("arial.ttf", size)
            else:
                return ImageFont.truetype("arial.ttf", size)
        except:
            try:
                if bold:
                    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
                else:
                    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
            except:
                return ImageFont.load_default()
    
    def gerar_qr_code(self, morador):
        """Gerar QR Code para validação da carteirinha"""
        dados_qr = {
            'id': morador.id,
            'nome': morador.nome_completo,
            'apartamento': f"{morador.bloco}-{morador.apartamento}",
            'validade': morador.data_vencimento.strftime('%Y-%m-%d') if morador.data_vencimento else None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(dados_qr, ensure_ascii=False))
            qr.make(fit=True)
            
            # Criar imagem diretamente
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Criar nova imagem PIL RGB
            rgb_img = Image.new('RGB', (200, 200), 'white')
            
            # Se o QR code foi gerado com sucesso, tentar usar
            try:
                # Usar o método padrão do PIL para redimensionar
                temp_img = qr_img.resize((200, 200))
                if hasattr(temp_img, 'mode') and temp_img.mode == 'RGB':
                    return temp_img
                else:
                    # Converter para RGB se necessário
                    rgb_img.paste(temp_img)
                    return rgb_img
            except:
                # Se falhar, criar QR code simples
                draw = ImageDraw.Draw(rgb_img)
                draw.rectangle([10, 10, 190, 190], outline='black', width=2)
                draw.text((50, 95), "QR CODE", fill='black')
                return rgb_img
                
        except Exception:
            # Fallback completo
            fallback_img = Image.new('RGB', (200, 200), 'white')
            draw = ImageDraw.Draw(fallback_img)
            draw.rectangle([10, 10, 190, 190], outline='black', width=2)
            draw.text((50, 95), "QR CODE", fill='black')
            return fallback_img
    
    def redimensionar_foto(self, foto_path, tamanho=(200, 250)):
        """Redimensionar e ajustar foto do morador"""
        try:
            with Image.open(foto_path) as img:
                # Converter para RGB se necessário
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar mantendo proporção
                img.thumbnail(tamanho, Image.Resampling.LANCZOS)
                
                # Criar nova imagem com fundo branco
                nova_img = Image.new('RGB', tamanho, 'white')
                
                # Centralizar a imagem
                x = (tamanho[0] - img.width) // 2
                y = (tamanho[1] - img.height) // 2
                nova_img.paste(img, (x, y))
                
                return nova_img
        except Exception as e:
            print(f"Erro ao processar foto: {e}")
            return self._criar_foto_placeholder(tamanho)
    
    def _criar_foto_placeholder(self, tamanho=(200, 250)):
        """Criar placeholder quando não há foto"""
        img = Image.new('RGB', tamanho, '#f8f9fa')
        draw = ImageDraw.Draw(img)
        
        # Desenhar ícone de usuário simples
        centro_x, centro_y = tamanho[0] // 2, tamanho[1] // 2
        raio = min(tamanho) // 4
        
        # Círculo da cabeça
        draw.ellipse([centro_x - raio//2, centro_y - raio, 
                     centro_x + raio//2, centro_y], fill='#dee2e6')
        
        # Corpo
        draw.ellipse([centro_x - raio, centro_y + raio//2, 
                     centro_x + raio, centro_y + raio*2], fill='#dee2e6')
        
        return img
    
    def gerar_carteirinha(self, morador, condominio=None):
        """Gerar carteirinha com design simples e limpo baseado na imagem de referência"""
        # Criar imagem base
        img = Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), '#ffffff')
        draw = ImageDraw.Draw(img)
        
        # Fontes
        fonte_titulo = self._get_font(24, bold=True)
        fonte_subtitulo = self._get_font(16, bold=True)
        fonte_nome = self._get_font(20, bold=True)
        fonte_dados = self._get_font(14)
        fonte_pequena = self._get_font(12)
        
        # Cores do condomínio (se disponível)
        if condominio:
            cor_primaria = condominio.cor_primaria or "#1e3a8a"
            cor_secundaria = condominio.cor_secundaria or "#3b82f6"
        else:
            cor_primaria = "#1e3a8a"  # Azul escuro
            cor_secundaria = "#3b82f6"  # Azul médio
        
        # === HEADER AZUL SUPERIOR ===
        header_height = 120
        
        # Fundo azul sólido no header
        draw.rectangle([0, 0, self.CARD_WIDTH, header_height], fill=cor_primaria)
        
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
        if condominio and condominio.nome:
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
            bbox = draw.textbbox((0, 0), teste_linha, font=fonte_titulo)
            largura_teste = bbox[2] - bbox[0]
            
            if largura_teste <= (self.CARD_WIDTH - titulo_x - 20):
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
        
        # Carregar foto do morador
        foto_path = None
        if hasattr(morador, 'anexos') and morador.anexos.first():
            anexo = morador.anexos.first()
            foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                   f'morador_{morador.id}', anexo.nome_arquivo)
        
        if foto_path and os.path.exists(foto_path):
            foto = self.redimensionar_foto(foto_path, foto_size)
        else:
            foto = self._criar_foto_placeholder(foto_size)
        
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
        qr_img = self.gerar_qr_code(morador)
        qr_size = 120
        qr_x = self.CARD_WIDTH - qr_size - 40
        qr_y = main_y + 20
        
        # Moldura do QR Code
        draw.rectangle([qr_x - 5, qr_y - 5, qr_x + qr_size + 5, qr_y + qr_size + 5], 
                      fill='white', outline='#cccccc', width=2)
        
        # Redimensionar e colar QR Code
        try:
            qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        except:
            qr_resized = Image.new('RGB', (qr_size, qr_size), 'white')
            draw_qr = ImageDraw.Draw(qr_resized)
            draw_qr.rectangle([10, 10, qr_size-10, qr_size-10], outline='black', width=2)
            draw_qr.text((qr_size//3, qr_size//2), "QR CODE", fill='black')
        
        img.paste(qr_resized, (qr_x, qr_y))
        
        # Label do QR Code
        qr_label = "CÓDIGO DE VERIFICAÇÃO"
        bbox = draw.textbbox((0, 0), qr_label, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
        label_x = qr_x + (qr_size - text_width) // 2
        label_y = qr_y + qr_size + 10
        draw.text((label_x, label_y), qr_label, fill='#666666', font=fonte_pequena)
        
        # === FOOTER ===
        footer_height = 50
        footer_y = self.CARD_HEIGHT - footer_height
        
        # Linha separadora
        draw.line([(20, footer_y), (self.CARD_WIDTH - 20, footer_y)], fill='#cccccc', width=2)
        
        # ID da carteirinha
        id_text = f"ID: {morador.id:05d}"
        draw.text((30, footer_y + 15), id_text, fill='#666666', font=fonte_pequena)
        
        # Data de emissão centralizada
        emissao_text = f"Emitida em {datetime.now().strftime('%d/%m/%Y')}"
        bbox = draw.textbbox((0, 0), emissao_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
        center_x = (self.CARD_WIDTH - text_width) // 2
        draw.text((center_x, footer_y + 15), emissao_text, fill='#666666', font=fonte_pequena)
        
        # Texto "DOCUMENTO OFICIAL"
        oficial_text = "DOCUMENTO OFICIAL"
        bbox = draw.textbbox((0, 0), oficial_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
        draw.text((self.CARD_WIDTH - text_width - 30, footer_y + 15), oficial_text, fill='#666666', font=fonte_pequena)
        
        # === BORDA FINAL ===
        draw.rectangle([0, 0, self.CARD_WIDTH-1, self.CARD_HEIGHT-1], 
                      outline='#cccccc', width=2)
        
        return img
    
    def gerar_carteirinha_pdf(self, morador, condominio=None):
        """Gerar carteirinha em PDF para impressão"""
        # Gerar imagem da carteirinha
        img = self.gerar_carteirinha(morador, condominio)
        
        # Criar PDF
        buffer = io.BytesIO()
        
        # Tamanho da página (A4)
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Salvar imagem temporariamente
        temp_img = io.BytesIO()
        img.save(temp_img, format='PNG')
        temp_img.seek(0)
        
        # Calcular posição centralizada
        card_width_mm = 85.6
        card_height_mm = 53.98
        
        card_width_points = card_width_mm * mm
        card_height_points = card_height_mm * mm
        
        x = (width - card_width_points) / 2
        y = (height - card_height_points) / 2
        
        # Adicionar imagem ao PDF
        c.drawImage(temp_img, x, y, card_width_points, card_height_points)
        
        # Linha de corte (opcional)
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
    
    def gerar_lote_carteirinhas(self, moradores, condominio=None):
        """Gerar múltiplas carteirinhas em um PDF"""  
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Dimensões da carteirinha em pontos
        card_width_mm = 85.6
        card_height_mm = 53.98
        card_width_points = card_width_mm * mm
        card_height_points = card_height_mm * mm
        
        # Margens
        margin = 20 * mm
        
        # Calcular quantas carteirinhas cabem por página (2 colunas x 4 linhas = 8 por página)
        cards_per_row = 2
        cards_per_col = 4
        cards_per_page = cards_per_row * cards_per_col
        
        for i, morador in enumerate(moradores):
            # Nova página se necessário
            if i > 0 and i % cards_per_page == 0:
                c.showPage()
            
            # Posição da carteirinha na página
            row = (i % cards_per_page) // cards_per_row
            col = (i % cards_per_page) % cards_per_row
            
            x = margin + col * (card_width_points + 10)  # 10 pontos de espaçamento
            y = height - margin - (row + 1) * (card_height_points + 10)  # 10 pontos de espaçamento
            
            # Gerar imagem da carteirinha
            img = self.gerar_carteirinha(morador, condominio)
            temp_img = io.BytesIO()
            img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            # Adicionar ao PDF
            c.drawImage(temp_img, x, y, card_width_points, card_height_points)
            
            # Linha de corte pontilhada
            c.setStrokeColor(HexColor('#cccccc'))
            c.setLineWidth(0.5)
            c.setDash([2, 2])  # Linha pontilhada
            c.rect(x, y, card_width_points, card_height_points)
            c.setDash([])  # Voltar linha sólida
        
        c.save()
        buffer.seek(0)
        return buffer

# Instância global do gerador
carteirinha_generator = CarteirinhaGenerator() 