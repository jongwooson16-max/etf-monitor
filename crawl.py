"""
ETF 모니터 — 네이버금융 자동 수집 스크립트
매주 GitHub Actions에서 자동 실행됩니다.
"""
 
import json
import time
import re
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError
 
# ── 모니터링 ETF 목록 ──────────────────────────────────────────
ETF_LIST = [
    {"id": "e01", "code": "314250", "name": "KODEX 미국빅테크10(H)",             "cat": "us",  "dist": "월"},
    {"id": "e02", "code": "396500", "name": "TIGER 반도체TOP10",                 "cat": "kr",  "dist": "분기"},
    {"id": "e03", "code": "0173Y0", "name": "KODEX 미국AI광통신네트워크",         "cat": "us",  "dist": "월"},
    {"id": "e04", "code": "458730", "name": "TIGER 미국배당다우존스",             "cat": "div", "dist": "월"},
    {"id": "e05", "code": "441640", "name": "KODEX 미국배당커버드콜액티브",       "cat": "div", "dist": "월"},
    {"id": "e06", "code": "395400", "name": "KODEX 한국부동산리츠인프라",         "cat": "re",  "dist": "월"},
    {"id": "e07", "code": "494300", "name": "KODEX 나스닥100데일리커버드콜OTM",   "cat": "cc",  "dist": "월"},
    {"id": "e08", "code": "498410", "name": "KODEX 금융고배당TOP10위클리커버드콜","cat": "cc",  "dist": "주간"},
    {"id": "e09", "code": "0167A0", "name": "SOL AI반도체TOP2플러스",             "cat": "kr",  "dist": "분기"},
    {"id": "e10", "code": "0190C0", "name": "RISE 현대차고정피지컬AI",            "cat": "kr",  "dist": "분기"},
    {"id": "e11", "code": "489030", "name": "PLUS 고배당주위클리커버드콜",        "cat": "cc",  "dist": "주간"},
    {"id": "e12", "code": "483570", "name": "KODEX 방산TOP10",                   "cat": "kr",  "dist": "분기"},
    {"id": "e13", "code": "0190D0", "name": "RISE AI전력인프라",                  "cat": "kr",  "dist": "분기"},
    {"id": "e14", "code": "491290", "name": "KODEX 조선TOP10",                   "cat": "kr",  "dist": "분기"},
    {"id": "e15", "code": "305720", "name": "KODEX 2차전지산업",                  "cat": "kr",  "dist": "분기"},
    {"id": "e16", "code": "483280", "name": "KODEX 미국AI테크TOP10타겟커버드콜", "cat": "cc",  "dist": "월"},
]
 
# ── 네이버금융 크롤링 ──────────────────────────────────────────
def fetch_naver(code: str) -> dict:
    """네이버금융에서 ETF 현재가·등락률·거래량 수집"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://finance.naver.com/",
    }
 
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("euc-kr", errors="replace")
    except URLError as e:
        print(f"  [오류] {code}: {e}")
        return {}
 
    result = {}
 
    # 현재가
    m = re.search(r'<p class="no_today">\s*<em[^>]*>\s*<span[^>]*>([^<]+)</span>', html)
    if not m:
        m = re.search(r'"현재가"[^>]*>\s*([\d,]+)', html)
    if m:
        result["price"] = m.group(1).strip().replace(",", "")
 
    # 등락률
    m = re.search(r'<em id="_rate"[^>]*><span[^>]*>([+-]?[\d.]+)</span>', html)
    if not m:
        m = re.search(r'등락률.*?([+-]?[\d.]+)%', html)
    if m:
        result["chg"] = m.group(1).strip()
 
    # 등락 방향(상승/하락)
    if "상승" in html[:3000] or 'class="up"' in html:
        result["chg_dir"] = "up"
    elif "하락" in html[:3000] or 'class="dn"' in html:
        result["chg_dir"] = "dn"
    else:
        result["chg_dir"] = "flat"
 
    # 52주 최고/최저 (있으면)
    m = re.search(r'52주\s*최고.*?<strong[^>]*>([\d,]+)', html)
    if m:
        result["w52_high"] = m.group(1).replace(",", "")
    m = re.search(r'52주\s*최저.*?<strong[^>]*>([\d,]+)', html)
    if m:
        result["w52_low"] = m.group(1).replace(",", "")
 
    return result
 
 
def fetch_naver_etf_detail(code: str) -> dict:
    """네이버금융 ETF 상세 페이지에서 NAV·순자산·분배금 수집"""
    url = f"https://finance.naver.com/fund/etfItemDetail.naver?etfItemId={code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://finance.naver.com/",
    }
 
    result = {}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("euc-kr", errors="replace")
    except URLError:
        return result
 
    # NAV
    m = re.search(r'NAV.*?<strong[^>]*>([\d,\.]+)', html, re.S)
    if m:
        result["nav"] = m.group(1).replace(",", "")
 
    # 순자산총액
    m = re.search(r'순자산총액.*?<strong[^>]*>([\d,\.]+)', html, re.S)
    if m:
        result["aum"] = m.group(1).replace(",", "")
 
    # 최근 분배금
    m = re.search(r'분배금.*?<td[^>]*>([\d,\.]+)원', html, re.S)
    if m:
        result["dist"] = m.group(1).replace(",", "")
 
    return result
 
 
# ── 메인 ──────────────────────────────────────────────────────
def main():
    kst = timezone(timedelta(hours=9))
    now_str = datetime.now(kst).strftime("%Y-%m-%d %H:%M KST")
    print(f"\n{'='*50}")
    print(f"ETF 데이터 수집 시작: {now_str}")
    print(f"{'='*50}")
 
    # 기존 data.json 로드 (PER·PBR 등 수동 입력값 보존)
    try:
        with open("data/etf_data.json", "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_map = {e["id"]: e for e in existing.get("etfs", [])}
    except FileNotFoundError:
        existing_map = {}
        print("  기존 데이터 없음 — 새로 생성합니다.")
 
    results = []
 
    for etf in ETF_LIST:
        code = etf["code"]
        name = etf["name"]
        print(f"\n  [{code}] {name}")
 
        # 기존 데이터 (수동 입력 PER·PBR 보존)
        prev = existing_map.get(etf["id"], {})
 
        # 네이버 크롤링
        main_data   = fetch_naver(code)
        detail_data = fetch_naver_etf_detail(code)
 
        # 합산
        fetched = {**main_data, **detail_data}
 
        if fetched.get("price"):
            print(f"    현재가: {fetched['price']}원  등락: {fetched.get('chg','?')}%")
        else:
            print(f"    ⚠ 가격 수집 실패 — 이전 값 유지")
 
        entry = {
            **etf,
            # 자동 수집값 (새 값 우선, 실패시 이전값 유지)
            "price":    fetched.get("price")    or prev.get("price", ""),
            "chg":      fetched.get("chg")      or prev.get("chg", ""),
            "chg_dir":  fetched.get("chg_dir")  or prev.get("chg_dir", "flat"),
            "nav":      fetched.get("nav")       or prev.get("nav", ""),
            "aum":      fetched.get("aum")       or prev.get("aum", ""),
            "w52_high": fetched.get("w52_high")  or prev.get("w52_high", ""),
            "w52_low":  fetched.get("w52_low")   or prev.get("w52_low", ""),
            # 수동 입력값 — 크롤링으로 덮어쓰지 않음
            "dist":     fetched.get("dist")      or prev.get("dist", ""),
            "per":      prev.get("per", ""),   # 수동 보존
            "pbr":      prev.get("pbr", ""),   # 수동 보존
            # 메타
            "updated":  now_str,
            "fetch_ok": bool(fetched.get("price")),
        }
        results.append(entry)
 
        time.sleep(0.8)   # 네이버 서버 부하 방지
 
    # 저장
    import os
    os.makedirs("data", exist_ok=True)
 
    output = {
        "updated": now_str,
        "total": len(results),
        "success": sum(1 for e in results if e["fetch_ok"]),
        "etfs": results,
    }
 
    with open("data/etf_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
 
    print(f"\n{'='*50}")
    print(f"완료: {output['success']}/{output['total']}개 수집 성공")
    print(f"저장: data/etf_data.json")
    print(f"{'='*50}\n")
 
 
if __name__ == "__main__":
    main()
