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
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        # Garantir que retorne PIL Image
        if hasattr(qr_img, 'convert'):
            return qr_img
        else:
            # Converter para PIL Image se necessário
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                qr_img.save(tmp.name)
                return Image.open(tmp.name).copy()
    
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
        """Gerar carteirinha completa do morador"""
        # Criar imagem base
        img = Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), self.COR_FUNDO)
        draw = ImageDraw.Draw(img)
        
        # Fontes
        fonte_titulo = self._get_font(24, bold=True)
        fonte_nome = self._get_font(20, bold=True)
        fonte_dados = self._get_font(14)
        fonte_pequena = self._get_font(10)
        
        # Cores do condomínio (se disponível)
        if condominio:
            cor_primaria = condominio.cor_primaria or self.COR_PRIMARIA
            cor_secundaria = condominio.cor_secundaria or self.COR_SECUNDARIA
        else:
            cor_primaria = self.COR_PRIMARIA
            cor_secundaria = self.COR_SECUNDARIA
        
        # === HEADER ===
        header_height = 80
        draw.rectangle([0, 0, self.CARD_WIDTH, header_height], fill=cor_primaria)
        
        # Título
        titulo = "CARTEIRINHA DA PISCINA"
        if condominio and condominio.nome:
            nome_cond = condominio.nome.upper()
            if len(nome_cond) > 25:
                nome_cond = nome_cond[:25] + "..."
            titulo = nome_cond
        
        bbox = draw.textbbox((0, 0), titulo, font=fonte_titulo)
        text_width = bbox[2] - bbox[0]
        x = (self.CARD_WIDTH - text_width) // 2
        draw.text((x, 25), titulo, fill='white', font=fonte_titulo)
        
        # === FOTO ===
        foto_size = (180, 220)
        foto_x, foto_y = 50, header_height + 30
        
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
        
        img.paste(foto, (foto_x, foto_y))
        
        # Borda na foto
        draw.rectangle([foto_x-2, foto_y-2, foto_x+foto_size[0]+2, foto_y+foto_size[1]+2], 
                      outline=cor_secundaria, width=3)
        
        # === DADOS DO MORADOR ===
        dados_x = foto_x + foto_size[0] + 40
        dados_y = header_height + 50
        
        # Nome (quebrar em linhas se muito longo)
        nome = morador.nome_completo.upper()
        if len(nome) > 20:
            palavras = nome.split()
            linha1 = ' '.join(palavras[:len(palavras)//2])
            linha2 = ' '.join(palavras[len(palavras)//2:])
            draw.text((dados_x, dados_y), linha1, fill=self.COR_TEXTO, font=fonte_nome)
            draw.text((dados_x, dados_y + 25), linha2, fill=self.COR_TEXTO, font=fonte_nome)
            dados_y += 60
        else:
            draw.text((dados_x, dados_y), nome, fill=self.COR_TEXTO, font=fonte_nome)
            dados_y += 35
        
        # Apartamento
        apt_text = f"BLOCO {morador.bloco} - APT {morador.apartamento}"
        draw.text((dados_x, dados_y), apt_text, fill=cor_primaria, font=fonte_dados)
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
        qr_img = self.gerar_qr_code(morador)
        qr_size = 120
        # Garantir que seja PIL Image antes de redimensionar
        if hasattr(qr_img, 'resize'):
            qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        else:
            qr_resized = qr_img.convert('RGB').resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_x = self.CARD_WIDTH - qr_size - 40
        qr_y = header_height + 40
        img.paste(qr_resized, (qr_x, qr_y))
        
        # Label QR Code
        draw.text((qr_x, qr_y + qr_size + 10), "VERIFICAÇÃO", 
                 fill=self.COR_TEXTO, font=fonte_pequena)
        
        # === FOOTER ===
        footer_y = self.CARD_HEIGHT - 60
        draw.rectangle([0, footer_y, self.CARD_WIDTH, self.CARD_HEIGHT], fill=cor_secundaria)
        
        # ID da carteirinha
        id_text = f"ID: {morador.id:04d}"
        draw.text((20, footer_y + 15), id_text, fill='white', font=fonte_pequena)
        
        # Data de emissão
        emissao_text = f"EMITIDA EM: {datetime.now().strftime('%d/%m/%Y')}"
        bbox = draw.textbbox((0, 0), emissao_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
        draw.text((self.CARD_WIDTH - text_width - 20, footer_y + 15), 
                 emissao_text, fill='white', font=fonte_pequena)
        
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