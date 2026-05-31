"""
邮件发送脚本 - 用于 GitHub Action 发送分析报告

功能：
1. 读取"宽基指数趋势大模型_EMA.py"生成的文本文件作为邮件正文
2. 将"基金趋势大模型_WMA.py"生成的 Excel 文件和图片打包成 zip 作为附件
3. 通过 QQ邮箱 SMTP 发送邮件

使用方式：
    python send_email.py --to recipient@qq.com \\
        --body-file 宽基指数分析结果.txt \\
        --attach-excel 基金趋势分析.xlsx \\
        --attach-images-dir 基金趋势图_20250101

环境变量（GitHub Secrets）：
    MAIL_USERNAME: QQ邮箱地址
    MAIL_PASSWORD: QQ邮箱SMTP授权码
    MAIL_TO: 收件人邮箱地址
"""

import smtplib
import os
import sys
import zipfile
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def create_zip_attachment(file_paths: list, zip_name: str = "附件.zip") -> str:
    """
    将多个文件打包成 zip 文件
    
    Args:
        file_paths: 要打包的文件路径列表
        zip_name: 生成的 zip 文件名
    
    Returns:
        str: 生成的 zip 文件路径
    """
    zip_path = os.path.join(os.path.dirname(file_paths[0]) if file_paths else '.', zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in file_paths:
            if os.path.exists(file_path):
                # 将文件添加到 zip 中，使用文件名（不含路径）
                arcname = os.path.basename(file_path)
                zf.write(file_path, arcname)
                print(f"  已添加至zip: {arcname}")
            else:
                print(f"  警告: 文件不存在 - {file_path}")
    
    return zip_path


def send_email(to_addr: str, subject: str, body_text: str, 
               attachment_paths: list = None,
               smtp_server: str = "smtp.qq.com", 
               smtp_port: int = 465):
    """
    发送邮件
    
    Args:
        to_addr: 收件人邮箱
        subject: 邮件主题
        body_text: 邮件正文（纯文本）
        attachment_paths: 附件文件路径列表
        smtp_server: SMTP服务器地址
        smtp_port: SMTP服务器端口（QQ邮箱SSL端口465）
    """
    # 从环境变量获取邮箱配置
    from_addr = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    
    if not from_addr or not password:
        print("错误: 未设置 MAIL_USERNAME 或 MAIL_PASSWORD 环境变量")
        print("请在 GitHub 仓库设置中添加以下 Secrets:")
        print("  - MAIL_USERNAME: QQ邮箱地址")
        print("  - MAIL_PASSWORD: QQ邮箱SMTP授权码")
        sys.exit(1)
    
    # 创建邮件对象
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    
    # 添加正文（使用HTML格式美化）
    html_body = body_text.replace('\n', '<br>\n')
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; }}
            pre {{ 
                font-family: 'Consolas', 'Courier New', monospace; 
                font-size: 13px;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <pre>{html_body}</pre>
        <hr>
        <p style="color: #888; font-size: 12px;">
            本邮件由 GitHub Action 自动发送 | {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 添加附件
    if attachment_paths:
        for file_path in attachment_paths:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=('utf-8', '', os.path.basename(file_path))
                    )
                    msg.attach(attachment)
                    print(f"  已添加附件: {os.path.basename(file_path)}")
            else:
                print(f"  警告: 附件不存在 - {file_path}")
    
    # 发送邮件
    try:
        print(f"正在连接 {smtp_server}:{smtp_port}...")
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(from_addr, password)
            server.send_message(msg)
        print(f"邮件发送成功!")
        print(f"  发件人: {from_addr}")
        print(f"  收件人: {to_addr}")
        print(f"  主题: {subject}")
    except smtplib.SMTPAuthenticationError:
        print("错误: SMTP认证失败，请检查邮箱地址和授权码是否正确")
        print("提示: QQ邮箱授权码需要在QQ邮箱设置 -> 账户 -> POP3/SMTP服务 中生成")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 邮件发送失败 - {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='发送基金分析报告邮件')
    parser.add_argument('--to', default=os.environ.get('MAIL_TO'),
                        help='收件人邮箱地址（也可通过 MAIL_TO 环境变量设置）')
    parser.add_argument('--body-file', default='宽基指数分析结果.txt',
                        help='邮件正文文本文件路径')
    parser.add_argument('--attach-excel', default='基金趋势分析.xlsx',
                        help='要附加的Excel文件路径')
    parser.add_argument('--attach-images-dir', default=None,
                        help='要附加的图片目录路径（目录下的所有png文件将被打包成zip）')
    parser.add_argument('--output-dir', default='.',
                        help='输出文件所在目录')
    
    args = parser.parse_args()
    
    # 检查收件人
    to_addr = args.to
    if not to_addr:
        print("错误: 未指定收件人邮箱")
        print("请使用 --to 参数或设置 MAIL_TO 环境变量")
        sys.exit(1)
    
    output_dir = args.output_dir
    
    # 1. 读取邮件正文
    body_file = os.path.join(output_dir, args.body_file)
    if os.path.exists(body_file):
        with open(body_file, 'r', encoding='utf-8') as f:
            body_text = f.read()
        print(f"已读取正文文件: {body_file}")
    else:
        print(f"警告: 正文文件不存在 - {body_file}，将使用默认正文")
        body_text = f"宽基指数趋势分析报告\n日期: {datetime.now().strftime('%Y-%m-%d')}\n\n（分析结果文件未生成）"
    
    # 2. 准备附件
    attachment_paths = []
    
    # 添加Excel文件
    excel_path = os.path.join(output_dir, args.attach_excel)
    if os.path.exists(excel_path):
        attachment_paths.append(excel_path)
        print(f"已找到Excel文件: {excel_path}")
    else:
        print(f"警告: Excel文件不存在 - {excel_path}")
    
    # 添加图片目录（打包成zip）
    if args.attach_images_dir:
        images_dir = os.path.join(output_dir, args.attach_images_dir)
        if os.path.isdir(images_dir):
            png_files = [os.path.join(images_dir, f) for f in os.listdir(images_dir) 
                        if f.endswith('.png')]
            if png_files:
                zip_path = create_zip_attachment(png_files, "基金趋势图.zip")
                attachment_paths.append(zip_path)
                print(f"已创建图片zip包: {zip_path} ({len(png_files)}张图片)")
            else:
                print(f"警告: 目录 {images_dir} 中没有PNG图片")
        else:
            print(f"警告: 图片目录不存在 - {images_dir}")
    
    # 3. 发送邮件
    today = datetime.now().strftime('%Y-%m-%d')
    subject = f'【基金趋势分析报告】{today}'
    
    send_email(
        to_addr=to_addr,
        subject=subject,
        body_text=body_text,
        attachment_paths=attachment_paths
    )


if __name__ == "__main__":
    main()
