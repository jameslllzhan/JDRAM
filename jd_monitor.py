import os
import requests
from bs4 import BeautifulSoup
import json

# 从环境变量读取配置
SCKEY = os.getenv('SCKEY')
SKU_ID = os.getenv('SKU_ID')
PRICE_THRESHOLD = float(os.getenv('PRICE_THRESHOLD', '9999'))

if not SCKEY or not SKU_ID:
    print("❌ 请在 GitHub Secrets 中设置 SCKEY 和 SKU_ID")
    exit(1)

# 京东商品页 URL
url = f"https://item.jd.com/{SKU_ID}.html"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 方法1：尝试从 JSON-LD 中提取价格（更稳定）
    price = None
    for script in soup.find_all("script"):
        if script.string and '"price"' in script.string:
            try:
                data = json.loads(script.string.strip())
                if isinstance(data, dict) and 'price' in data:
                    price = data['price']
                    break
            except:
                continue

    # 方法2：备用，从页面元素提取
    if not price:
        price_elem = soup.find('span', class_='price')
        if price_elem:
            price_text = price_elem.get_text().strip('¥')
            price = price_text.split('\n')[0]  # 可能有多个价格，取第一个

    if not price:
        raise Exception("未能提取价格")

    current_price = float(price)
    print(f"✅ 商品 {SKU_ID} 当前价格：¥{current_price}")

    if current_price <= PRICE_THRESHOLD:
        title = "💰 价格达标提醒！"
        desp = f"商品 [京东链接](https://item.jd.com/{SKU_ID}.html) 当前价格：**¥{current_price}**\n\n目标价：¥{PRICE_THRESHOLD}"
        push_url = f"https://sctapi.ftqq.com/{SCKEY}.send"
        requests.post(push_url, data={"title": title, "desp": desp})
        print("✅ 已发送微信提醒！")
    else:
        print(f"⏳ 未达目标价（目标 ¥{PRICE_THRESHOLD}）")

except Exception as e:
    print(f"❌ 监控失败: {e}")
    # 可选：失败也推送（调试用）
    # requests.post(f"https://sctapi.ftqq.com/{SCKEY}.send", data={"title": "监控失败", "desp": str(e)})
