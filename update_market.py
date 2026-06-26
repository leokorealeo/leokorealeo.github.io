# -*- coding: utf-8 -*-
"""
증시 데이터를 야후 파이낸스에서 받아 market.json 으로 저장한다.
GitHub Actions(서버)에서 실행되므로 CORS 제약이 없고 API 키도 필요 없다.
페이지(index.html)는 같은 주소의 market.json 만 읽으면 된다.
"""
import urllib.request
import urllib.parse
import json
import datetime

# (표시이름, 분류, 야후심볼, 소수자리, 그룹)
SYMBOLS = [
    ("코스피",     "한국",   "^KS11",     2, "indices"),
    ("코스닥",     "한국",   "^KQ11",     2, "indices"),
    ("S&P 500",    "미국",   "^GSPC",     2, "indices"),
    ("나스닥",     "미국",   "^IXIC",     2, "indices"),
    ("닛케이225",  "일본",   "^N225",     2, "indices"),
    ("USD/KRW",    "환율",   "KRW=X",     2, "indices"),
    ("삼성전자",   "반도체", "005930.KS", 0, "stocks"),
    ("SK하이닉스", "반도체", "000660.KS", 0, "stocks"),
    ("NVIDIA",     "AI",     "NVDA",      2, "stocks"),
    ("비트코인",   "코인",   "BTC-USD",   0, "stocks"),
]


def fmt(n, dec):
    return f"{n:,.{dec}f}"


def fmt_signed(n, dec):
    sign = "+" if n > 0 else ("-" if n < 0 else "")
    return sign + f"{abs(n):,.{dec}f}"


def fetch(symbol):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    meta = data["chart"]["result"][0]["meta"]
    price = meta["regularMarketPrice"]
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    change = price - prev
    pct = (change / prev) * 100 if prev else 0.0
    return price, change, pct


def main():
    indices, stocks = [], []
    for name, cat, sym, dec, grp in SYMBOLS:
        try:
            price, change, pct = fetch(sym)
            item = {
                "name": name,
                "category": cat,
                "value": fmt(price, dec),
                "change": fmt_signed(change, dec),
                "changePercent": f"{pct:.2f}",
            }
            (indices if grp == "indices" else stocks).append(item)
        except Exception as e:  # noqa: BLE001
            print(f"skip {name}: {e}")

    now_utc = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    out = {
        "updatedAt": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "indices": indices,
        "stocks": stocks,
    }
    with open("market.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote market.json with {len(indices) + len(stocks)} items")


if __name__ == "__main__":
    main()
