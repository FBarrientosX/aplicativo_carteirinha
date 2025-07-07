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
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(dados_qr, ensure_ascii=False))
        qr.make(fit=True)
        
        # Gerar imagem do QR Code e garantir compatibilidade
        try:
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Criar uma nova imagem PIL RGB garantida
            rgb_img = Image.new('RGB', (200, 200), 'white')
            
            # Tentar redimensionar e colar a imagem do QR
            try:
                # Verificar se o objeto tem método resize
                if hasattr(qr_img, 'resize') and callable(getattr(qr_img, 'resize')):
                    qr_resized = qr_img.resize((200, 200), Image.Resampling.LANCZOS)
                    rgb_img.paste(qr_resized)
                else:
                    # Se não tem resize, criar nova imagem e colar
                    if hasattr(qr_img, 'size'):
                        temp_img = Image.new('RGB', qr_img.size, 'white')
                        temp_img.paste(qr_img)
                        qr_resized = temp_img.resize((200, 200), Image.Resampling.LANCZOS)
                        rgb_img.paste(qr_resized)
                    else:
                        # Fallback: desenhar QR code simples
                        draw = ImageDraw.Draw(rgb_img)
                        draw.rectangle([10, 10, 190, 190], outline='black', width=3)
                        draw.text((70, 95), "QR CODE", fill='black')
            except Exception:
                # Se falhar, desenhar um QR code simples
                draw = ImageDraw.Draw(rgb_img)
                draw.rectangle([10, 10, 190, 190], outline='black', width=3)
                draw.text((70, 95), "QR CODE", fill='black')
            
            return rgb_img
            
        except Exception:
            # Fallback completo se tudo falhar
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
        """Gerar carteirinha completa do morador com design moderno"""
        # Criar imagem base
        img = Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), '#ffffff')
        draw = ImageDraw.Draw(img)
        
        # Fontes
        fonte_titulo = self._get_font(32, bold=True)
        fonte_subtitulo = self._get_font(20, bold=True)
        fonte_nome = self._get_font(28, bold=True)
        fonte_dados = self._get_font(18, bold=True)
        fonte_pequena = self._get_font(16)
        fonte_micro = self._get_font(12)
        fonte_extra_pequena = self._get_font(10)
        
        # Cores do condomínio (se disponível)
        if condominio:
            cor_primaria = condominio.cor_primaria or "#1976d2"
            cor_secundaria = condominio.cor_secundaria or "#42a5f5"
        else:
            cor_primaria = "#1976d2"  # Azul moderno
            cor_secundaria = "#42a5f5"  # Azul claro
        
        # === FUNDO COM PADRÃO GEOMÉTRICO MODERNO ===
        # Gradiente de fundo sofisticado
        for y in range(self.CARD_HEIGHT):
            for x in range(self.CARD_WIDTH):
                # Gradiente diagonal complexo
                factor_x = x / self.CARD_WIDTH
                factor_y = y / self.CARD_HEIGHT
                
                # Criar padrão de ondas sutis
                wave_factor = 0.02 * (factor_x + factor_y)
                
                r = int(248 + wave_factor * 20)
                g = int(252 + wave_factor * 15)
                b = int(255 + wave_factor * 10)
                
                # Adicionar textura pontilhada sutil
                if (x + y) % 80 == 0:
                    r = min(255, r + 5)
                    g = min(255, g + 5)
                    b = min(255, b + 5)
                
                draw.point((x, y), (r, g, b))
        
        # === PADRÃO DECORATIVO DE FUNDO ===
        # Círculos decorativos sutis
        for i in range(0, self.CARD_WIDTH, 120):
            for j in range(0, self.CARD_HEIGHT, 120):
                # Círculos grandes muito sutis
                draw.ellipse([i-30, j-30, i+30, j+30], outline='#f0f4f8', width=1)
                draw.ellipse([i-15, j-15, i+15, j+15], outline='#e3f2fd', width=1)
        
        # === HEADER PRINCIPAL MODERNO ===
        header_height = 140
        
        # Gradiente vibrante no header (similar à imagem de referência)
        base_color = tuple(int(cor_primaria.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        for y in range(header_height):
            alpha = y / header_height
            
            # Gradiente com múltiplas camadas
            if alpha < 0.3:
                factor = alpha / 0.3
                r = int(base_color[0] * (1 + factor * 0.1))
                g = int(base_color[1] * (1 + factor * 0.15))
                b = int(base_color[2] * (1 + factor * 0.2))
            elif alpha < 0.7:
                factor = (alpha - 0.3) / 0.4
                r = int(base_color[0] * 1.1 * (1 - factor * 0.1))
                g = int(base_color[1] * 1.15 * (1 - factor * 0.1))
                b = int(base_color[2] * 1.2 * (1 - factor * 0.1))
            else:
                factor = (alpha - 0.7) / 0.3
                r = int(base_color[0] * (1 - factor * 0.2))
                g = int(base_color[1] * (1 - factor * 0.2))
                b = int(base_color[2] * (1 - factor * 0.2))
            
            # Garantir que os valores estejam no range válido
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            draw.line([(0, y), (self.CARD_WIDTH, y)], fill=(r, g, b))
        
        # === ELEMENTOS DECORATIVOS NO HEADER ===
        # Padrão de ondas no header
        for x in range(0, self.CARD_WIDTH, 60):
            wave_y = 15 + int(10 * (x / self.CARD_WIDTH))
            draw.ellipse([x-3, wave_y, x+3, wave_y+6], fill='#ffffff30')
            
            wave_y2 = header_height - 25 - int(8 * ((self.CARD_WIDTH - x) / self.CARD_WIDTH))
            draw.ellipse([x-2, wave_y2, x+2, wave_y2+4], fill='#ffffff20')
        
        # === LOGO/ÍCONE MODERNO ===
        # Círculo principal do logo (similar à imagem de referência)
        logo_x, logo_y = 40, 25
        logo_size = 80
        
        # Gradiente no logo
        for i in range(logo_size//2):
            alpha = i / (logo_size//2)
            r = int(255 * (1 - alpha * 0.3))
            g = int(255 * (1 - alpha * 0.2))
            b = int(255 * (1 - alpha * 0.1))
            
            draw.ellipse([logo_x + i, logo_y + i, 
                         logo_x + logo_size - i, logo_y + logo_size - i], 
                        outline=(r, g, b), width=2)
        
        # Ícone central do logo
        center_x, center_y = logo_x + logo_size//2, logo_y + logo_size//2
        
        # Desenhar ondas estilizadas (representando piscina)
        for i in range(3):
            wave_offset = i * 8
            draw.arc([center_x - 20 + wave_offset, center_y - 15, 
                     center_x + 20 + wave_offset, center_y + 15], 
                    start=0, end=180, fill='white', width=3)
        
        # === TÍTULO PRINCIPAL ===
        if condominio and condominio.nome:
            titulo = condominio.nome.upper()
            if len(titulo) > 20:
                titulo = titulo[:20] + "..."
        else:
            titulo = "MEU CONDOMÍNIO"
        
        # Posicionar título ao lado do logo
        titulo_x = logo_x + logo_size + 30
        titulo_y = logo_y + 10
        
        # Sombra do título
        draw.text((titulo_x + 3, titulo_y + 3), titulo, fill='#00000040', font=fonte_titulo)
        draw.text((titulo_x, titulo_y), titulo, fill='white', font=fonte_titulo)
        
        # === SUBTÍTULO ESTILIZADO ===
        subtitulo = "CARTEIRINHA DA PISCINA"
        subtitulo_y = titulo_y + 45
        
        # Fundo decorativo para o subtítulo
        bbox = draw.textbbox((0, 0), subtitulo, font=fonte_subtitulo)
        text_width = bbox[2] - bbox[0]
        
        # Retângulo com cantos arredondados (simulado)
        rect_x1, rect_y1 = titulo_x - 5, subtitulo_y - 5
        rect_x2, rect_y2 = titulo_x + text_width + 5, subtitulo_y + 30
        
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill='#ffffff40', outline='white', width=2)
        draw.text((titulo_x, subtitulo_y), subtitulo, fill='white', font=fonte_subtitulo)
        
        # === LINHA DECORATIVA INFERIOR DO HEADER ===
        line_y = header_height - 10
        # Linha principal
        draw.rectangle([20, line_y, self.CARD_WIDTH - 20, line_y + 4], fill='#ffffff80')
        # Linha secundária
        draw.rectangle([40, line_y + 6, self.CARD_WIDTH - 40, line_y + 8], fill='#ffffff60')
        
        # === ÁREA PRINCIPAL COM LAYOUT MODERNO ===
        main_y = header_height + 30
        
        # === FOTO COM DESIGN PREMIUM ===
        foto_size = (200, 240)
        foto_x, foto_y = 50, main_y
        
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
        
        # === MOLDURA SOFISTICADA DA FOTO ===
        # Múltiplas sombras para profundidade
        for i in range(8, 0, -1):
            shadow_alpha = 20 - (i * 2)
            shadow_color = f'#000000{shadow_alpha:02x}'
            draw.rectangle([foto_x + i, foto_y + i, 
                           foto_x + foto_size[0] + i, foto_y + foto_size[1] + i], 
                          fill=shadow_color)
        
        # Moldura principal
        draw.rectangle([foto_x - 6, foto_y - 6, 
                       foto_x + foto_size[0] + 6, foto_y + foto_size[1] + 6], 
                      fill='white', outline=cor_primaria, width=4)
        
        # Moldura interna
        draw.rectangle([foto_x - 3, foto_y - 3, 
                       foto_x + foto_size[0] + 3, foto_y + foto_size[1] + 3], 
                      outline='#e0e0e0', width=2)
        
        img.paste(foto, (foto_x, foto_y))
        
        # === PAINEL DE INFORMAÇÕES MODERNO ===
        info_x = foto_x + foto_size[0] + 40
        info_y = main_y
        info_width = 420
        info_height = 240
        
        # Fundo do painel com gradiente sutil
        for y in range(info_height):
            alpha = y / info_height
            r = int(255 - alpha * 8)
            g = int(255 - alpha * 5)
            b = int(255 - alpha * 3)
            draw.line([(info_x, info_y + y), (info_x + info_width, info_y + y)], fill=(r, g, b))
        
        # Bordas do painel
        draw.rectangle([info_x - 3, info_y - 3, info_x + info_width + 3, info_y + info_height + 3], 
                      outline=cor_primaria, width=3)
        draw.rectangle([info_x, info_y, info_x + info_width, info_y + info_height], 
                      outline='#e0e0e0', width=1)
        
        # === NOME DO MORADOR ===
        nome_y = info_y + 20
        nome = morador.nome_completo.upper()
        
        # Fundo para o nome (similar ao design da referência)
        nome_bg_height = 50
        draw.rectangle([info_x + 15, nome_y - 10, info_x + info_width - 15, nome_y + nome_bg_height], 
                      fill=cor_primaria, outline='white', width=2)
        
        # Adicionar padrão decorativo no fundo do nome
        for i in range(info_x + 20, info_x + info_width - 20, 30):
            draw.ellipse([i, nome_y + 5, i + 4, nome_y + 9], fill='#ffffff30')
        
        # Renderizar nome (quebrar em linhas se necessário)
        if len(nome) > 18:
            palavras = nome.split()
            meio = len(palavras) // 2
            linha1 = ' '.join(palavras[:meio])
            linha2 = ' '.join(palavras[meio:])
            
            # Centralizar texto
            bbox1 = draw.textbbox((0, 0), linha1, font=fonte_nome)
            bbox2 = draw.textbbox((0, 0), linha2, font=fonte_nome)
            x1 = info_x + (info_width - (bbox1[2] - bbox1[0])) // 2
            x2 = info_x + (info_width - (bbox2[2] - bbox2[0])) // 2
            
            draw.text((x1, nome_y), linha1, fill='white', font=fonte_nome)
            draw.text((x2, nome_y + 32), linha2, fill='white', font=fonte_nome)
            nome_y += 75
        else:
            bbox = draw.textbbox((0, 0), nome, font=fonte_nome)
            x = info_x + (info_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, nome_y + 10), nome, fill='white', font=fonte_nome)
            nome_y += 65
        
        # === INFORMAÇÕES ORGANIZADAS ===
        info_start_y = nome_y + 10
        
        # Lista de informações com ícones e cores
        info_items = [
            ("🏢", f"BLOCO {morador.bloco} • APARTAMENTO {morador.apartamento}", cor_primaria),
            ("👤", "TITULAR" if morador.eh_titular else "DEPENDENTE", cor_secundaria),
        ]
        
        # Validade com cor dinâmica
        if morador.data_vencimento:
            validade_text = f"VÁLIDA ATÉ {morador.data_vencimento.strftime('%d/%m/%Y')}"
            cor_validade = '#d32f2f' if morador.status_carteirinha == 'vencida' else '#2e7d32'
        else:
            validade_text = "VALIDADE NÃO DEFINIDA"
            cor_validade = '#f57c00'
        
        info_items.append(("📅", validade_text, cor_validade))
        
        # Status com emoji
        status_map = {
            'regular': ('✅', 'CARTEIRINHA REGULAR', '#2e7d32'),
            'a_vencer': ('⚠️', 'A VENCER EM BREVE', '#f57c00'),
            'vencida': ('❌', 'CARTEIRINHA VENCIDA', '#d32f2f'),
            'sem_carteirinha': ('⚠️', 'SEM CARTEIRINHA', '#757575')
        }
        icone, status_text, cor_status = status_map.get(morador.status_carteirinha, ('❓', 'STATUS INDEFINIDO', '#757575'))
        info_items.append((icone, status_text, cor_status))
        
        # Renderizar informações com design moderno
        for i, (emoji, texto, cor) in enumerate(info_items):
            item_y = info_start_y + (i * 42)
            
            # Fundo alternado para cada item
            if i % 2 == 0:
                draw.rectangle([info_x + 10, item_y - 8, info_x + info_width - 10, item_y + 30], 
                              fill='#f8f9fa', outline='#e9ecef', width=1)
            
            # Círculo para o emoji/ícone
            circle_x = info_x + 25
            draw.ellipse([circle_x, item_y, circle_x + 28, item_y + 28], 
                        fill='white', outline=cor, width=3)
            draw.text((circle_x + 6, item_y + 4), emoji, font=fonte_dados)
            
            # Texto da informação
            draw.text((info_x + 65, item_y + 6), texto, fill=cor, font=fonte_dados)
        
        # === QR CODE MODERNO ===
        qr_img = self.gerar_qr_code(morador)
        qr_size = 180
        qr_x = self.CARD_WIDTH - qr_size - 70
        qr_y = main_y + 20
        
        # Fundo decorativo para o QR Code (similar à imagem de referência)
        qr_bg_size = qr_size + 50
        qr_bg_x = qr_x - 25
        qr_bg_y = qr_y - 25
        
        # Gradiente circular para o fundo do QR
        center_qr_x = qr_bg_x + qr_bg_size // 2
        center_qr_y = qr_bg_y + qr_bg_size // 2
        
        for i in range(qr_bg_size // 2):
            alpha = i / (qr_bg_size // 2)
            r = int(240 + alpha * 15)
            g = int(245 + alpha * 10)
            b = int(250 + alpha * 5)
            
            draw.ellipse([center_qr_x - i, center_qr_y - i, 
                         center_qr_x + i, center_qr_y + i], 
                        outline=(r, g, b), width=1)
        
        # Moldura do QR Code
        draw.rectangle([qr_x - 10, qr_y - 10, qr_x + qr_size + 10, qr_y + qr_size + 10], 
                      fill='white', outline=cor_primaria, width=5)
        draw.rectangle([qr_x - 5, qr_y - 5, qr_x + qr_size + 5, qr_y + qr_size + 5], 
                      outline='#e0e0e0', width=2)
        
        # Redimensionar e colar QR Code
        try:
            qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        except:
            qr_resized = Image.new('RGB', (qr_size, qr_size), 'white')
            draw_qr = ImageDraw.Draw(qr_resized)
            draw_qr.rectangle([20, 20, qr_size-20, qr_size-20], outline='black', width=4)
            draw_qr.text((qr_size//3, qr_size//2), "QR CODE", fill='black')
        
        img.paste(qr_resized, (qr_x, qr_y))
        
        # Label do QR Code
        qr_label = "VERIFICAÇÃO DIGITAL"
        bbox = draw.textbbox((0, 0), qr_label, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
        label_x = qr_x + (qr_size - text_width) // 2
        label_y = qr_y + qr_size + 25
        
        # Fundo para o label
        draw.rectangle([label_x - 8, label_y - 5, label_x + text_width + 8, label_y + 22], 
                      fill=cor_primaria, outline='white', width=2)
        draw.text((label_x, label_y), qr_label, fill='white', font=fonte_pequena)
        
        # === FOOTER MODERNO ===
        footer_height = 70
        footer_y = self.CARD_HEIGHT - footer_height
        
        # Gradiente no footer
        footer_color = tuple(int(cor_secundaria.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        for y in range(footer_height):
            alpha = y / footer_height
            r = int(footer_color[0] * (1 + alpha * 0.3))
            g = int(footer_color[1] * (1 + alpha * 0.3))
            b = int(footer_color[2] * (1 + alpha * 0.3))
            
            # Garantir range válido
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            draw.line([(0, footer_y + y), (self.CARD_WIDTH, footer_y + y)], fill=(r, g, b))
        
        # Padrão decorativo no footer
        for x in range(0, self.CARD_WIDTH, 40):
            draw.ellipse([x-2, footer_y+8, x+2, footer_y+12], fill='#ffffff40')
            draw.ellipse([x-2, footer_y+footer_height-12, x+2, footer_y+footer_height-8], fill='#ffffff40')
        
        # === INFORMAÇÕES DO FOOTER ===
        # ID da carteirinha
        id_text = f"ID: {morador.id:05d}"
        draw.text((30, footer_y + 20), id_text, fill='white', font=fonte_pequena)
        
        # Data de emissão centralizada
        emissao_text = f"EMITIDA EM {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        bbox = draw.textbbox((0, 0), emissao_text, font=fonte_pequena)
        text_width = bbox[2] - bbox[0]
        center_x = (self.CARD_WIDTH - text_width) // 2
        draw.text((center_x, footer_y + 20), emissao_text, fill='white', font=fonte_pequena)
        
        # Selo de autenticidade moderno
        selo_x = self.CARD_WIDTH - 150
        selo_y = footer_y + 15
        
        # Círculo do selo
        draw.ellipse([selo_x, selo_y, selo_x + 35, selo_y + 35], 
                    fill='#ffffff50', outline='white', width=3)
        
        # Texto do selo
        draw.text((selo_x + 45, footer_y + 15), "DOCUMENTO", fill='white', font=fonte_extra_pequena)
        draw.text((selo_x + 45, footer_y + 28), "OFICIAL", fill='white', font=fonte_extra_pequena)
        draw.text((selo_x + 45, footer_y + 41), f"v{datetime.now().year}", fill='white', font=fonte_extra_pequena)
        
        # Marca d'água no selo
        draw.text((selo_x + 8, selo_y + 12), "★", fill='white', font=fonte_pequena)
        
        # === BORDAS FINAIS ===
        # Borda principal
        draw.rectangle([0, 0, self.CARD_WIDTH-1, self.CARD_HEIGHT-1], 
                      outline=cor_primaria, width=4)
        # Borda interna
        draw.rectangle([3, 3, self.CARD_WIDTH-4, self.CARD_HEIGHT-4], 
                      outline='#e0e0e0', width=2)
        
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