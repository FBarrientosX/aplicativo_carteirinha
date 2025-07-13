from app import create_app, db
from app.models import *
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        print("✅ Banco de dados verificado/criado!")
    
    # Configuração para produção
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("🌐 Servidor iniciando...")
    if debug:
        print("📱 Para acessar pelo celular, use o IP do seu computador")
        print("🔗 Exemplo: http://192.168.0.5:5000")
        print("📷 QR Scanner com upload de imagem disponível como alternativa")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )