# Serviço de envio de mensagens via WhatsApp (stub)
# Substitua por integração real (ex.: API oficial WhatsApp Business, Gupshup, Zenvia etc.)

import logging
from datetime import datetime


def send_whatsapp_message(phone_number: str, message: str) -> tuple[bool, str | None]:
    """
    Envia mensagem de WhatsApp (stub).
    Retorna (sucesso, erro).
    """
    try:
        if not phone_number:
            return False, "Telefone não informado"
        # Aqui entraria a chamada real da API
        logging.info(f"[WhatsApp] {datetime.now()} → Para: {phone_number} | Msg: {message}")
        return True, None
    except Exception as e:
        logging.exception("Erro ao enviar WhatsApp")
        return False, str(e)
