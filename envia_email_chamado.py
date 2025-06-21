import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from deep_translator import GoogleTranslator


def enviar_email_fechamento(email_destinatario, id_chamado, estado, data_fechamento, usuario_fechamento):
    remetente = "jonathanwillian710@gmail.com"
    senha = "ipwz cujh frdv ivjj"
    
    assunto = f"Chamado {id_chamado} - Fechado"
    corpo = f"""
    Olá,
    
    Informamos que o chamado {id_chamado} foi fechado.
    
    Estado: {GoogleTranslator(source='auto', target='pt').translate(estado)}
    Data do fechamento: {data_fechamento}
    Fechado por: {usuario_fechamento}
    
    Caso precise de mais informações, entre em contato.
    
    Atenciosamente,
    Equipe de Suporte
    """
   

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = email_destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, email_destinatario, msg.as_string())
        print(f"✅ E-mail de fechamento enviado para {email_destinatario}")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {str(e)}")