from app import create_app, db
from app.models import *

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        print("✅ Banco de dados verificado/criado!")
    
    # Configuração para aceitar conexões externas (celular)
    print("🌐 Servidor iniciando...")
    print("📱 Para acessar pelo celular, use o IP do seu computador")
    print("🔗 Exemplo: http://192.168.0.5:5000")
    print("📷 QR Scanner com upload de imagem disponível como alternativa")
    
    app.run(
        host='0.0.0.0',  # Aceita conexões de qualquer IP
        port=5000,       # Porta padrão
        debug=True
    )