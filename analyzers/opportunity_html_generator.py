"""创业机会分析 HTML 生成器"""


def generate_opportunity_html(markdown_content):
    """将 Markdown 机会分析转为 HTML"""
    import re

    lines = markdown_content.split("\n")
    html_parts = []

    html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>创业机会 & 工作提效分析</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; line-height: 1.6; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #58a6ff; font-size: 1.8em; margin: 20px 0 10px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }
        h2 { color: #58a6ff; font-size: 1.4em; margin: 30px 0 12px; }
        h3 { color: #79c0ff; font-size: 1.1em; margin: 16px 0 8px; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        p { margin: 8px 0; }
        ul { padding-left: 20px; }
        li { margin: 4px 0; }
        hr { border: none; border-top: 1px solid #21262d; margin: 20px 0; }
        .summary { background: #161b22; padding: 16px; border-radius: 8px; margin: 16px 0; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #8b949e; }
    </style>
</head>
<body>
<div class="container">""")

    html_parts.append('<a href="index.html" class="back-link">← 返回趋势总览</a>')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            html_parts.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_parts.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_parts.append(f"<h3>{_parse_inline_links(line[4:])}</h3>")
        elif line.startswith("**") and line.endswith("**"):
            html_parts.append(f'<p><strong>{line[2:-2]}</strong></p>')
        elif line.startswith("- "):
            html_parts.append(f"<li>{_parse_inline_links(line[2:])}</li>")
        elif line.startswith("---"):
            html_parts.append("<hr>")
        else:
            html_parts.append(f"<p>{_parse_inline_links(line)}</p>")

    html_parts.append("</div></body></html>")

    return "\n".join(html_parts)


def _parse_inline_links(text):
    """解析 Markdown 内联链接 [text](url)"""
    import re
    return re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', text)
