import os
import requests
from ashare_data import get_index_quote

# 从 GitHub Actions 的环境变量中读取 Token
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN")

def fetch_indexes():
    """获取上证指数和深证成指收盘数据。"""
    indexes = {}
    # 000001 是上证指数，399001 是深证成指
    for code, name in [("000001", "上证指数"), ("399001", "深证成指")]:
        try:
            q = get_index_quote(code)
            indexes[name] = {
                "last": q.last,
                # 兼容不同版本的字段名
                "pct": getattr(q, "pct_chg", None) or getattr(q, "change_pct", None),
            }
        except Exception as e:
            indexes[name] = {"error": str(e)}
    return indexes

def build_content(indexes):
    """组装 Markdown 格式的推送内容。"""
    lines = [f"### 盘面速览", ""]
    for name, data in indexes.items():
        if "error" in data:
            lines.append(f"- **{name}**：获取失败（{data['error']}）")
        else:
            pct = data["pct"]
            # 如果获取到了涨跌幅，格式化一下（带 + 或 - 号）
            pct_str = f" ({pct:+.2f}%)" if isinstance(pct, (int, float)) else ""
            lines.append(f"- **{name}**：{data['last']}{pct_str}")
    return "\n".join(lines)

def send_to_pushplus(title, content):
    """通过 PushPlus 接口推送到微信。"""
    if not PUSHPLUS_TOKEN:
        raise ValueError("未找到 PUSHPLUS_TOKEN 环境变量，请检查 GitHub Secrets 配置")
        
    url = "https://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "markdown",
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 200:
            raise RuntimeError(f"PushPlus 返回异常: {body}")
        print("推送成功:", body.get("msg"))
    except Exception as e:
        print("推送失败:", e)
        raise e

if __name__ == "__main__":
    print("开始获取盘面数据...")
    indexes = fetch_indexes()
    
    print("开始组装内容...")
    content = build_content(indexes)
    print("推送内容如下：\n", content)
    
    print("正在推送到微信...")
    send_to_pushplus("今日盘面速览", content)
