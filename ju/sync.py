#!/usr/bin/env python3
"""
从金山文档抓取影视资源合集内容，生成 HTML 并推送到 GitHub Pages。

用法: python3 sync.py
依赖: pip install playwright && playwright install chromium
"""

import subprocess
import re
import os

# ============ 配置 ============
KDOCS_URL = "https://www.kdocs.cn/l/ceY4XreMYOc8"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
WEIBO_ID = "你的微博ID"  # 改成你的微博ID
WEIBO_URL = "#"           # 改成你的微博主页链接
# ==============================


def fetch_content():
    """用 playwright 抓取金山文档内容"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(KDOCS_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)  # 等待文档渲染

        text = page.evaluate("""() => {
            const editArea = document.querySelector('.container')
                || document.querySelector('#docx-container')
                || document.querySelector('[class*="doc"]');
            return editArea ? editArea.innerText : document.body.innerText;
        }""")

        browser.close()
    return text


def parse_entries(raw_text):
    """解析文档文本，提取每部剧的信息"""
    lines = raw_text.split('\n')
    entries = []
    current = None

    # 跳过头部信息的关键词
    skip_keywords = ['搜索方法', '解决办法', '教程', '影视资源合集', 'cloud', '创建',
                     '点赞', '留言', '发送', 'AI 总结', '仅查看', '今天 ', '昨天 ',
                     '更新', '‼️']

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过UI元素和说明文字
        if any(kw in line for kw in skip_keywords):
            continue

        # 检测网盘链接行
        quark_match = re.search(r'夸克网盘[：:]\s*(https://pan\.quark\.cn/\S+)', line)
        baidu_match = re.search(r'百度网盘[：:]\s*(https://pan\.baidu\.com/\S+)', line)
        ali_match = re.search(r'阿里云盘[：:]\s*(https://www\.ali(?:pan|yundrive)\.com/\S+)', line)

        if quark_match and current:
            current['quark'] = quark_match.group(1)
        elif baidu_match and current:
            current['baidu'] = baidu_match.group(1)
        elif ali_match and current:
            current['ali'] = ali_match.group(1)
        elif not quark_match and not baidu_match and not ali_match:
            # 可能是标题行
            # 去掉emoji前缀
            clean = re.sub(r'^[🔥⭐🎬📺\s]+', '', line)
            if not clean or len(clean) < 2:
                continue

            # 解析标签
            tags = []
            hot = False
            if '🔥' in line:
                hot = True

            # 提取方括号和圆括号中的标签
            bracket_tags = re.findall(r'[【（(]([^】）)]+)[】）)]', clean)
            title_part = re.split(r'[【（(]', clean)[0].strip()

            if not title_part or len(title_part) < 2:
                continue

            # 分类标签
            quality_tags = []
            lang_tags = []
            type_tags = []
            season_info = ''

            for tag in bracket_tags:
                tag_lower = tag.lower()
                if any(q in tag_lower for q in ['4k', '1080', '高清', 'hdr']):
                    quality_tags.append(tag)
                elif any(l in tag_lower for l in ['中英', '双语', '双字', '字幕']):
                    lang_tags.append(tag)
                elif any(t in tag_lower for t in ['美剧', '英剧', '韩剧', '日剧', '电影', '动漫', '纪录片']):
                    type_tags.append(tag)
                elif any(s in tag_lower for s in ['季', '全集', '特别篇', '重生']):
                    season_info = tag
                else:
                    quality_tags.append(tag)

            # 保存当前条目
            if current:
                entries.append(current)

            current = {
                'title': title_part,
                'season': season_info,
                'hot': hot,
                'quality_tags': quality_tags,
                'lang_tags': lang_tags,
                'type_tags': type_tags,
                'quark': '',
                'baidu': '',
                'ali': '',
            }

    if current:
        entries.append(current)

    return entries


def generate_html(entries):
    """生成 HTML 页面"""
    cards_html = ""
    for entry in entries:
        title_display = entry['title']
        if entry['season']:
            title_display += f" 【{entry['season']}】"

        fire = '<span class="fire"></span>' if entry['hot'] else ''

        tags_html = ""
        for t in entry['quality_tags']:
            tags_html += f'      <span class="tag tag-quality">{t}</span>\n'
        for t in entry['lang_tags']:
            tags_html += f'      <span class="tag tag-lang">{t}</span>\n'
        for t in entry['type_tags']:
            tags_html += f'      <span class="tag tag-type">{t}</span>\n'

        links_html = ""
        if entry['quark']:
            links_html += f'      <a class="link-btn link-quark" href="{entry["quark"]}" target="_blank">夸克网盘</a>\n'
        if entry['baidu']:
            links_html += f'      <a class="link-btn link-baidu" href="{entry["baidu"]}" target="_blank">百度网盘</a>\n'
        if entry['ali']:
            links_html += f'      <a class="link-btn link-ali" href="{entry["ali"]}" target="_blank">阿里云盘</a>\n'

        cards_html += f"""
  <div class="card" data-title="{entry['title']}">
    <div class="card-title">{fire}{title_display}</div>
    <div class="card-tags">
{tags_html}    </div>
    <div class="links">
{links_html}    </div>
  </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>影视资源合集（持续更新）</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
  }}
  .header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 40px 20px;
    text-align: center;
  }}
  .header h1 {{ font-size: 28px; font-weight: 700; }}
  .header p {{ margin-top: 8px; opacity: 0.9; font-size: 14px; }}
  .notice {{
    max-width: 800px;
    margin: 20px auto;
    padding: 14px 20px;
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    border-radius: 6px;
    font-size: 14px;
  }}
  .notice strong {{ color: #856404; }}
  .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
  .card {{
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
  }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
  .card-title {{ font-size: 18px; font-weight: 600; margin-bottom: 6px; }}
  .card-title .fire::before {{ content: "\\01F525"; margin-right: 4px; }}
  .card-tags {{ margin-bottom: 10px; }}
  .tag {{
    display: inline-block;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 6px;
    margin-bottom: 4px;
  }}
  .tag-quality {{ background: #e8f5e9; color: #2e7d32; }}
  .tag-lang {{ background: #e3f2fd; color: #1565c0; }}
  .tag-type {{ background: #fce4ec; color: #c62828; }}
  .links {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .link-btn {{
    display: inline-flex;
    align-items: center;
    padding: 8px 16px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: opacity 0.2s;
  }}
  .link-btn:hover {{ opacity: 0.85; }}
  .link-quark {{ background: #6C5CE7; color: white; }}
  .link-baidu {{ background: #2196F3; color: white; }}
  .link-ali {{ background: #FF6B35; color: white; }}
  .footer {{
    text-align: center;
    padding: 30px 20px;
    font-size: 13px;
    color: #999;
  }}
  .footer a {{ color: #667eea; text-decoration: none; }}
  .search-box {{
    max-width: 800px;
    margin: 20px auto 0;
    padding: 0 20px;
  }}
  .search-box input {{
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    outline: none;
    transition: border-color 0.2s;
  }}
  .search-box input:focus {{ border-color: #667eea; }}
  .hidden {{ display: none !important; }}
  @media (max-width: 600px) {{
    .header h1 {{ font-size: 22px; }}
    .card {{ padding: 16px; }}
    .links {{ flex-direction: column; }}
    .link-btn {{ justify-content: center; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>影视资源合集</h1>
  <p>持续更新 · 收藏本页告别剧荒</p>
</div>

<div class="search-box">
  <input type="text" id="searchInput" placeholder="搜索片名..." oninput="filterCards()">
</div>

<div class="notice">
  <strong>使用方法：</strong>长按复制链接，在【夸克】或【百度网盘】APP 中打开，保存即可观看。
</div>

<div class="container" id="cardList">
{cards_html}
</div>

<div class="footer">
  <p>资源均来自网络，仅供学习交流</p>
  <p>更多资源请关注微博 <a href="{WEIBO_URL}">@{WEIBO_ID}</a></p>
</div>

<script>
function filterCards() {{
  const query = document.getElementById('searchInput').value.toLowerCase();
  document.querySelectorAll('.card').forEach(card => {{
    const title = card.getAttribute('data-title').toLowerCase();
    const text = card.innerText.toLowerCase();
    card.classList.toggle('hidden', query && !title.includes(query) && !text.includes(query));
  }});
}}
</script>

</body>
</html>"""
    return html


def git_push():
    """提交并推送到 GitHub"""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    cmds = [
        ["git", "add", "index.html"],
        ["git", "commit", "-m", "update: 同步影视资源合集"],
        ["git", "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)
        if result.returncode != 0 and "nothing to commit" not in result.stderr:
            print(f"  命令 {' '.join(cmd)} 输出: {result.stderr.strip()}")
        else:
            print(f"  ✓ {' '.join(cmd)}")


def main():
    print("1. 抓取金山文档内容...")
    raw = fetch_content()

    print("2. 解析资源条目...")
    entries = parse_entries(raw)
    print(f"   找到 {len(entries)} 部影视资源")

    print("3. 生成 HTML...")
    html = generate_html(entries)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   已写入 {OUTPUT_FILE}")

    print("4. 推送到 GitHub...")
    git_push()

    print("\n✅ 同步完成！")


if __name__ == "__main__":
    main()
