#!/usr/bin/env python3
"""
Script para adicionar a coluna tipo_anexo ao banco de dados
Execute este script quando o servidor Flask estiver parado.
"""

import sqlite3
import os
import sys

def adicionar_coluna_tipo_anexo():
    """Adiciona a coluna tipo_anexo ao banco de dados"""
    db_path = 'carteirinha_piscina.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        print("🔌 Conectando ao banco de dados...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(anexos_moradores)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'tipo_anexo' in columns:
            print("✅ Coluna tipo_anexo já existe!")
            conn.close()
            return True
        
        print("🔧 Adicionando coluna tipo_anexo...")
        
        # Adicionar a coluna
        cursor.execute('ALTER TABLE anexos_moradores ADD COLUMN tipo_anexo VARCHAR(20) DEFAULT "documento"')
        
        print("📝 Atualizando registros existentes...")
        
        # Definir primeiro anexo de imagem de cada morador como foto_carteirinha
        cursor.execute('''
            UPDATE anexos_moradores 
            SET tipo_anexo = 'foto_carteirinha' 
            WHERE tipo_arquivo IN ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp')
            AND id IN (
                SELECT MIN(id) 
                FROM anexos_moradores 
                WHERE tipo_arquivo IN ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp')
                GROUP BY morador_id
            )
        ''')
        
        fotos_atualizadas = cursor.rowcount
        
        # Garantir que outros anexos sejam marcados como documento
        cursor.execute('''
            UPDATE anexos_moradores 
            SET tipo_anexo = 'documento' 
            WHERE tipo_anexo = 'documento' OR tipo_anexo IS NULL
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Coluna adicionada com sucesso!")
        print(f"📸 {fotos_atualizadas} anexos definidos como foto_carteirinha")
        print(f"📄 Outros anexos definidos como documento")
        print("")
        print("🔄 Agora você pode:")
        print("   1. Descomentar a linha 'tipo_anexo' no modelo AnexoMorador")
        print("   2. Atualizar as propriedades para usar tipo_anexo")
        print("   3. Reiniciar o servidor Flask")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar banco: {e}")
        if 'conn' in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False

if __name__ == "__main__":
    print("🚀 Script para adicionar coluna tipo_anexo")
    print("⚠️  IMPORTANTE: Pare o servidor Flask antes de executar!")
    print("")
    
    resposta = input("Continuar? (s/N): ").lower().strip()
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada.")
        sys.exit(1)
    
    if adicionar_coluna_tipo_anexo():
        print("🎉 Banco de dados atualizado com sucesso!")
    else:
        print("💥 Falha ao atualizar o banco de dados.")
        sys.exit(1) 