"""
邮件发送脚本 - 用于 GitHub Action 发送分析报告

功能：
1. 读取"宽基指数趋势大模型_EMA.py"生成的文本文件作为邮件正文
2. 将"基金趋势大模型_WMA.py"生成的 Excel 文件作为附件
3. 在正文末尾添加趋势图下载链接（图片太大，通过 Artifact 下载）
4. 通过 SMTP 发送邮件（默认 QQ邮箱）

使用方式：
    python send_email.py --to recipient@qq.com \\
        --body-file 宽基指数分析结果.txt \\
        --attach-excel 基金趋势分析.xlsx \\
        --download-url "https://github.com/.../actions/runs/..."

环境变量（GitHub Secrets）：
    MAIL_USERNAME:   邮箱地址（必填）
    MAIL_PASSWORD:   邮箱SMTP授权码（必填）
    MAIL_TO:         收件人邮箱地址（必填）
    MAIL_SMTP_SERVER: SMTP服务器地址（可选，默认 smtp.qq.com）
    MAIL_SMTP_PORT:   SMTP服务器端口（可选，默认 465）
"""


import smtplib
import os
import sys
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def send_email(to_addr: str, subject: str, body_text: str, 
               attachment_paths: list = None,
               smtp_server: str = None, 
               smtp_port: int = None):
    """
    发送邮件
    
    Args:
        to_addr: 收件人邮箱
        subject: 邮件主题
        body_text: 邮件正文（纯文本）
        attachment_paths: 附件文件路径列表
        smtp_server: SMTP服务器地址（默认从环境变量 MAIL_SMTP_SERVER 读取，否则使用 smtp.qq.com）
        smtp_port: SMTP服务器端口（默认从环境变量 MAIL_SMTP_PORT 读取，否则使用 465）
    """
    # 从环境变量获取邮箱配置
    from_addr = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    
    # SMTP 服务器配置：参数 > 环境变量 > 默认值
    if smtp_server is None:
        smtp_server = os.environ.get('MAIL_SMTP_SERVER', 'smtp.qq.com')
    if smtp_port is None:
        smtp_port = int(os.environ.get('MAIL_SMTP_PORT', '465'))

    
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
    
    # 添加附件（仅限小文件，如Excel）
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
    parser.add_argument('--to', default=None,
                        help='收件人邮箱地址（也可通过 MAIL_TO 环境变量设置）')
    parser.add_argument('--body-file', default='宽基指数分析结果.txt',
                        help='邮件正文文本文件路径')
    parser.add_argument('--attach-excel', default='基金趋势分析.xlsx',
                        help='要附加的Excel文件路径')
    parser.add_argument('--download-url', default=None,
                        help='趋势图下载链接（GitHub Artifact URL，会追加到正文末尾）')
    parser.add_argument('--output-dir', default='.',
                        help='输出文件所在目录')
    
    args = parser.parse_args()
    
    # 检查收件人：优先使用 --to 参数，其次环境变量
    to_addr = args.to or os.environ.get('MAIL_TO')
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
    
    # 2. 在正文末尾添加趋势图下载链接
    if args.download_url:
        body_text += f"""
═══════════════════════════════════════════
📊 基金趋势图下载
═══════════════════════════════════════════
趋势图文件较大，已上传至 GitHub Artifact，
请点击下方链接下载（需登录 GitHub 账号）：

{args.download_url}

下载后解压即可查看各基金的趋势分析图表。
═══════════════════════════════════════════
"""
        print(f"已添加趋势图下载链接: {args.download_url}")
    
    # 3. 准备附件（仅Excel，不包含图片）
    attachment_paths = []
    
    excel_path = os.path.join(output_dir, args.attach_excel)
    if os.path.exists(excel_path):
        attachment_paths.append(excel_path)
        print(f"已找到Excel文件: {excel_path}")
    else:
        print(f"警告: Excel文件不存在 - {excel_path}")
    
    # 4. 发送邮件
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
