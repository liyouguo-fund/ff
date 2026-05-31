# 基金趋势分析报告 - GitHub Action 自动发送

## 📋 项目简介

本项目每天北京时间 **9:00** 自动运行两个分析脚本，并通过 **QQ邮箱** 发送分析报告邮件：

1. **宽基指数趋势大模型_EMA.py** - 分析宽基指数/ETF趋势（结果作为邮件正文）
2. **基金趋势大模型_WMA.py** - 分析场外基金趋势（Excel + 趋势图作为附件）

分析结果会自动推送到仓库，方便历史追溯。

## 🚀 部署步骤

### 1. 推送到 GitHub

```bash
# 克隆仓库
git clone https://github.com/liyouguo-fund/ff.git
cd ff

# 将本项目所有文件复制到仓库目录
# （将本目录下的所有文件复制到 ff 目录）

# 提交推送
git add .
git commit -m "初始化：基金趋势分析系统"
git push -u origin main
```

### 2. 配置 GitHub Secrets

在 GitHub 仓库页面：**Settings → Secrets and variables → Actions → New repository secret**

需要添加以下 4 个 Secrets：

| Secret 名称 | 必填 | 说明 | 示例值 |
|------------|------|------|--------|
| `MAIL_USERNAME` | ✅ | QQ邮箱地址 | `123456789@qq.com` |
| `MAIL_PASSWORD` | ✅ | QQ邮箱SMTP授权码 | `xxxxxxxxxxxxxx` |
| `MAIL_TO` | ✅ | 收件人邮箱地址 | `your-email@qq.com` |
| `WENCAI_QUERY` | ❌ | 问财查询语句（不填则使用默认值） | `近一年涨幅前10名，C类基金` |

> **如何获取 QQ邮箱 SMTP 授权码？**
> 1. 登录 QQ邮箱 → 设置 → 账户
> 2. 找到 "POP3/SMTP服务" 或 "IMAP/SMTP服务"
> 3. 点击 "开启"（需要手机验证）
> 4. 按提示发送短信后，会生成一个 **授权码**（16位字母）
> 5. 将此授权码填入 `MAIL_PASSWORD` Secret

> **关于 WENCAI_QUERY（可选）**
> 如果不设置此 Secret，脚本默认使用 `近一年涨幅前5名，C类基金`。
> 你可以自定义问财查询语句，例如：
> - `近一年涨幅前10名，C类基金`
> - `近6月涨幅前20名，C类基金，规模大于1亿`
> - `近3年收益前10名，C类基金`

### 3. 验证部署

1. 进入 GitHub 仓库 → **Actions** 标签页
2. 你会看到 "每日基金趋势分析报告" workflow
3. 点击 **Run workflow** → 选择 **workflow_dispatch** → 点击绿色按钮手动触发一次
4. 等待运行完成，检查邮箱是否收到报告邮件

### 4. 定时执行

Workflow 已配置为每天 **北京时间 9:00** 自动执行（对应 UTC 时间 1:00）。

> ⚠️ **注意**：GitHub Actions 的定时任务可能会有几分钟的延迟，这是正常现象。

## 📁 文件结构

```
ff/
├── .github/workflows/
│   └── daily_report.yml    # GitHub Action 配置文件
├── 宽基指数趋势大模型_EMA.py  # 宽基指数分析脚本
├── 基金趋势大模型_WMA.py      # 场外基金分析脚本
├── send_email.py            # 邮件发送脚本
├── requirements.txt         # Python 依赖
└── README.md               # 本文件
```

## 🔧 自定义配置

### 修改分析时间

编辑 `.github/workflows/daily_report.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 1 * * *'   # UTC 1:00 = 北京时间 9:00
```

cron 格式：`分钟 小时 日 月 星期`
- 例如 `0 9 * * 1-5` = 工作日北京时间 17:00

### 修改问财查询语句

方式一（推荐）：在 GitHub Secrets 中设置 `WENCAI_QUERY`
方式二：直接修改 `基金趋势大模型_WMA.py` 中的默认值

### 修改宽基指数列表

编辑 `宽基指数趋势大模型_EMA.py` 中的 `indices` 列表，添加/删除要分析的指数。

## 📧 邮件内容说明

- **邮件正文**：宽基指数趋势分析结果（表格形式）
- **邮件附件**：
  - `基金趋势分析.xlsx` - 所有基金指标数据
  - `基金趋势图.zip` - 各基金的趋势分析图表

## ❓ 常见问题

**Q: 邮件发送失败？**
A: 检查 GitHub Secrets 中的 `MAIL_PASSWORD` 是否为 QQ邮箱授权码（不是QQ密码）。

**Q: 中文显示为乱码？**
A: Workflow 已自动安装中文字体，如果仍有问题，请检查 matplotlib 配置。

**Q: 如何查看运行日志？**
A: 在 GitHub → Actions → 点击具体运行记录 → 查看各步骤日志。

**Q: 推送失败（Permission denied）？**
A: 确保仓库的 Actions 有写入权限：
   1. 进入 Settings → Actions → General
   2. 在 "Workflow permissions" 中勾选 "Read and write permissions"
   3. 勾选 "Allow GitHub Actions to create and approve pull requests"
