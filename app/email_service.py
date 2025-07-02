from flask_mail import Message
from flask import current_app, render_template
from app import mail, db
from app.models import Morador, LogNotificacao
from datetime import datetime, timedelta
import logging

def enviar_email(assunto, destinatario, template_html, template_text=None, **kwargs):
    """Função genérica para envio de emails"""
    try:
        # Carregar configurações de email do banco de dados
        from app.models import ConfiguracaoSistema
        from app import app
        
        mail_server = ConfiguracaoSistema.get_valor('MAIL_SERVER')
        mail_username = ConfiguracaoSistema.get_valor('MAIL_USERNAME') 
        mail_password = ConfiguracaoSistema.get_valor('MAIL_PASSWORD')
        mail_default_sender = ConfiguracaoSistema.get_valor('MAIL_DEFAULT_SENDER')
        
        if not mail_server or not mail_username or not mail_password:
            return False, "❌ Configurações de email não encontradas! Configure primeiro em Configurações → Email."
        
        # Atualizar configurações da aplicação
        current_app.config.update({
            'MAIL_SERVER': mail_server,
            'MAIL_PORT': ConfiguracaoSistema.get_valor('MAIL_PORT', 587),
            'MAIL_USE_TLS': ConfiguracaoSistema.get_valor('MAIL_USE_TLS', True),
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': mail_username,
            'MAIL_PASSWORD': str(mail_password).strip().replace(' ', '') if mail_password else '',
            'MAIL_DEFAULT_SENDER': mail_default_sender or mail_username
        })
        
        # Reinicializar Flask-Mail
        mail.init_app(current_app)
        
        # Obter o sender das configurações atualizadas
        sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        
        msg = Message(
            assunto,
            sender=sender,
            recipients=[destinatario],
            html=render_template(template_html, **kwargs),
            body=render_template(template_text, **kwargs) if template_text else None
        )
        mail.send(msg)
        return True, None
    except Exception as e:
        erro_msg = str(e)
        
        # Melhorar mensagens de erro comuns
        if "530" in erro_msg and "Authentication Required" in erro_msg:
            erro_msg = "❌ Gmail requer Senha de App! Ative 2FA e gere uma senha específica em: myaccount.google.com/apppasswords"
        elif "535" in erro_msg and "authentication failed" in erro_msg.lower():
            erro_msg = "❌ Credenciais inválidas! Verifique email e senha."
        elif "550" in erro_msg:
            erro_msg = "❌ Email rejeitado pelo servidor. Verifique se o email de destino existe."
        elif "Connection refused" in erro_msg:
            erro_msg = "❌ Não foi possível conectar ao servidor SMTP. Verifique servidor e porta."
        
        logging.error(f"Erro ao enviar email para {destinatario}: {erro_msg}")
        return False, erro_msg

def enviar_notificacao_30_dias(morador):
    """Envia notificação 30 dias antes do vencimento"""
    if morador.notificacao_30_dias_enviada:
        return True, "Notificação já enviada"
    
    email_destino = morador.get_email_notificacao()
    
    sucesso, erro = enviar_email(
        assunto=f"Carteirinha da Piscina - Vence em {morador.dias_para_vencer} dias",
        destinatario=email_destino,
        template_html='email/notificacao_30_dias.html',
        template_text='email/notificacao_30_dias.txt',
        morador=morador
    )
    
    # Log da notificação (comentado temporariamente)
    # log = LogNotificacao(
    #     morador_id=morador.id,
    #     tipo_notificacao='30_dias',
    #     email_enviado=email_destino,
    #     status_envio='sucesso' if sucesso else 'erro',
    #     mensagem_erro=erro
    # )
    # db.session.add(log)
    
    if sucesso:
        morador.notificacao_30_dias_enviada = True
        db.session.commit()
    
    return sucesso, erro

def enviar_notificacao_vencimento(morador):
    """Envia notificação quando a carteirinha vence"""
    if morador.notificacao_vencimento_enviada:
        return True, "Notificação já enviada"
    
    email_destino = morador.get_email_notificacao()
    
    sucesso, erro = enviar_email(
        assunto="Carteirinha da Piscina - VENCIDA",
        destinatario=email_destino,
        template_html='email/notificacao_vencimento.html',
        template_text='email/notificacao_vencimento.txt',
        morador=morador
    )
    
    # Log da notificação (comentado temporariamente)
    # log = LogNotificacao(
    #     morador_id=morador.id,
    #     tipo_notificacao='vencimento',
    #     email_enviado=email_destino,
    #     status_envio='sucesso' if sucesso else 'erro',
    #     mensagem_erro=erro
    # )
    # db.session.add(log)
    
    if sucesso:
        morador.notificacao_vencimento_enviada = True
        morador.carteirinha_ativa = False
        db.session.commit()
    
    return sucesso, erro

def verificar_e_enviar_notificacoes():
    """Tarefa automatizada para verificar e enviar notificações"""
    hoje = datetime.now().date()
    
    # Buscar moradores que precisam de notificação de 30 dias
    moradores_30_dias = Morador.query.filter(
        Morador.data_vencimento == hoje + timedelta(days=30),
        Morador.notificacao_30_dias_enviada == False,
        Morador.carteirinha_ativa == True
    ).all()
    
    # Buscar moradores com carteirinha vencida hoje
    moradores_vencidos = Morador.query.filter(
        Morador.data_vencimento == hoje,
        Morador.notificacao_vencimento_enviada == False,
        Morador.carteirinha_ativa == True
    ).all()
    
    resultados = {
        'notificacoes_30_dias': 0,
        'notificacoes_vencimento': 0,
        'erros': []
    }
    
    # Enviar notificações de 30 dias
    for morador in moradores_30_dias:
        sucesso, erro = enviar_notificacao_30_dias(morador)
        if sucesso:
            resultados['notificacoes_30_dias'] += 1
        else:
            resultados['erros'].append(f"Erro 30 dias - {morador.nome_completo}: {erro}")
    
    # Enviar notificações de vencimento
    for morador in moradores_vencidos:
        sucesso, erro = enviar_notificacao_vencimento(morador)
        if sucesso:
            resultados['notificacoes_vencimento'] += 1
        else:
            resultados['erros'].append(f"Erro vencimento - {morador.nome_completo}: {erro}")
    
    logging.info(f"Notificações enviadas: {resultados}")
    return resultados

def enviar_email_boas_vindas(morador):
    """Envia email de boas-vindas para novo morador"""
    email_destino = morador.get_email_notificacao()
    
    sucesso, erro = enviar_email(
        assunto="Bem-vindo ao Sistema de Carteirinhas da Piscina",
        destinatario=email_destino,
        template_html='email/boas_vindas.html',
        template_text='email/boas_vindas.txt',
        morador=morador
    )
    
    return sucesso, erro 