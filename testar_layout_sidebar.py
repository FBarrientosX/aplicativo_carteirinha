#!/usr/bin/env python3
"""
Script para testar o novo layout com sidebar
"""

from app import create_app
import webbrowser
import time
from threading import Timer

def open_browser():
    """Abre o navegador após um delay"""
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

def main():
    """Função principal para testar o layout"""
    print("🚀 Testando novo layout com sidebar...")
    print("=" * 50)
    
    app = create_app()
    
    # Configurar para desenvolvimento
    app.config['DEBUG'] = True
    app.config['TESTING'] = False
    
    print("✅ Aplicação criada com sucesso!")
    print("📱 Novo layout com navegação lateral implementado")
    print("🎨 Estilos CSS atualizados")
    print("\n🔍 Funcionalidades do novo layout:")
    print("   • Navegação lateral fixa em desktop")
    print("   • Menu colapsável em mobile")
    print("   • Perfil do usuário na sidebar")
    print("   • Seções organizadas por módulo")
    print("   • Design moderno e responsivo")
    print("   • Animações e transições suaves")
    print("   • Scrollbar personalizada")
    print("   • Suporte a dark mode")
    
    print("\n🌐 Abrindo navegador...")
    print("📍 URL: http://127.0.0.1:5000")
    print("\n📋 Para testar:")
    print("   1. Faça login no sistema")
    print("   2. Teste a navegação lateral")
    print("   3. Redimensione a janela para testar responsividade")
    print("   4. Teste em mobile (F12 > Toggle device toolbar)")
    
    # Abrir navegador automaticamente
    Timer(1.0, open_browser).start()
    
    try:
        # Executar aplicação
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar aplicação: {str(e)}")
    
    print("\n✅ Teste concluído!")
    return 0

if __name__ == '__main__':
    exit(main())
