import email_config as config
import smtplib
from email.message import EmailMessage
from email.mime.image import MIMEImage
from typing import List
import os
import markdown

class EmailSender:
    def sendMarkdown(subject:str, bodyMarkdown:str, attachments:List[str]) -> None:
        EmailSender.send(subject, markdown.markdown(bodyMarkdown, extensions=['tables', 'sane_lists']), attachments)

    def send(subject:str, body:str, attachments:List[str]) -> None:
        try:
            server = smtplib.SMTP_SSL(config.email['smtp_host'], config.email['smtp_port'])
            server.ehlo()
            server.login(config.email['from'], config.email['password'])

            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = config.email['from']
            msg['To'] = config.email['to']

            msg.add_alternative(body, subtype='html')

            for attachment in attachments:
                with open(attachment, 'rb') as f:
                    img_data = f.read()
                msg.attach(MIMEImage(img_data, name=os.path.basename(attachment)))

            server.send_message(msg)

        except Exception as e:
            print(e)
        finally:
            server.quit()

if __name__ == "__main__":
    str = """
# Testing
| Column 1 | Column 2|
| --- | --- |
| 2 | 3.5 |
| 1 | Str |

## Test something else
* Bullet 1
\t* Subbullet 1.1
* Bullet 2
    """
    print(markdown.markdown(str, extensions=['tables', 'sane_lists']))
    #send_email('Testing 123',  markdown.markdown(str, extensions=['tables', 'sane_lists']), ['Plot 2021-01-01 to 2021-12-28.png'])
    EmailSender.send('Testing 123',  markdown.markdown(str, extensions=['tables', 'sane_lists']), [])