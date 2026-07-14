"""
ETF 모니터 — 네이버금융 자동 수집 스크립트
평일 16:00(KST) GitHub Actions에서 자동 실행됩니다.
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
    {"id": "e06", "code": "476800", "name": "KODEX 한국부동산리츠인프라",         "cat": "re",  "dist": "월"},
    {"id": "e07", "code": "494300", "name": "KODEX 나스닥100데일리커버드콜OTM",   "cat": "cc",  "dist": "월"},
    {"id": "e08", "code": "498410", "name": "KODEX 금융고배당TOP10위클리커버드콜","cat": "cc",  "dist": "주간"},
    {"id": "e09", "code": "0167A0", "name": "SOL AI반도체TOP2플러스",             "cat": "kr",  "dist": "분기"},
    {"id": "e10", "code": "0190C0", "name": "RISE 현대차고정피지컬AI",            "cat": "kr",  "dist": "분기"},
    {"id": "e11", "code": "489030", "name": "PLUS 고배당주위클리커버드콜",        "cat": "cc",  "dist": "주간"},
    {"id": "e12", "code": "0080G0", "name": "KODEX 방산TOP10",                   "cat": "kr",  "dist": "분기"},
    {"id": "e14", "code": "0115D0", "name": "KODEX 조선TOP10",                   "cat": "kr",  "dist": "분기"},  # 코드 오류 수정: 491290 -> 0115D0
    {"id": "e15", "code": "305720", "name": "KODEX 2차전지산업",                  "cat": "kr",  "dist": "분기"},
    {"id": "e16", "code": "483280", "name": "KODEX 미국AI테크TOP10타겟커버드콜", "cat": "cc",  "dist": "월"},
    {"id": "e17", "code": "069500", "name": "KODEX 200",                        "cat": "kr",  "dist": "분기"},
    {"id": "e18", "code": "0219E0", "name": "KODEX 200커버드콜액티브",           "cat": "cc",  "dist": "월"},
    {"id": "e19", "code": "498400", "name": "KODEX 200타겟위클리커버드콜",       "cat": "cc",  "dist": "월"},
    # e13 RISE AI전력인프라(0190D0)는 삭제됨
]
 
# ── 네이버금융 크롤링 ──────────────────────────────────────────
NAVER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://finance.naver.com/",
}
 
 
def fetch_etf_list_api() -> dict:
    """
    네이버금융 ETF 전체목록 JSON API 1회 호출로 현재가·NAV·순자산총액 등을 모두 수집.
    기존에는 종목별 상세페이지를 정규식으로 긁었는데 페이지 구조 변경으로 NAV/AUM이
    전혀 수집되지 않고 있었음. 이 API는 네이버 ETF 화면이 실제로 사용하는 데이터
    소스라 필드가 안정적으로 유지됨.
    반환: { code: {price, chg, chg_dir, nav, aum, volume} }
    """
    url = "https://finance.naver.com/api/sise/etfItemList.nhn"
    try:
        req = Request(url, headers=NAVER_HEADERS)
        with urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except (URLError, json.JSONDecodeError) as e:
        print(f"  [오류] ETF 목록 API 호출 실패: {e}")
        return {}
 
    items = data.get("result", {}).get("etfItemList", [])
    out = {}
    for it in items:
        code = str(it.get("itemcode", "")).strip()
        if not code:
            continue
 
        change_val = it.get("changeVal")
        rise_fall = str(it.get("risefall", ""))
        if rise_fall in ("1", "2"):
            chg_dir = "up"
        elif rise_fall in ("4", "5"):
            chg_dir = "dn"
        else:
            try:
                chg_dir = "up" if float(change_val) > 0 else ("dn" if float(change_val) < 0 else "flat")
            except (TypeError, ValueError):
                chg_dir = "flat"
 
        out[code] = {
            "price": str(it.get("nowVal", "") or ""),
            "chg": str(it.get("changeRate", "") or ""),
            "chg_dir": chg_dir,
            "nav": str(it.get("nav", "") or ""),
            "aum": str(it.get("marketSum", "") or ""),   # 억원 단위
            "volume": str(it.get("quant", "") or ""),
        }
    return out
 
 
def fetch_naver_w52(code: str) -> dict:
    """네이버금융 개별 종목 페이지에서 52주 최고/최저만 보조 수집 (실패해도 무방)"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    result = {}
    try:
        req = Request(url, headers=NAVER_HEADERS)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("euc-kr", errors="replace")
    except URLError as e:
        print(f"  [오류] {code} 52주 정보: {e}")
        return result
 
    m = re.search(r'52주\s*최고.*?<strong[^>]*>([\d,]+)', html, re.S)
    if m:
        result["w52_high"] = m.group(1).replace(",", "")
    m = re.search(r'52주\s*최저.*?<strong[^>]*>([\d,]+)', html, re.S)
    if m:
        result["w52_low"] = m.group(1).replace(",", "")
 
    # API 호출이 실패했을 때를 대비한 가격 폴백
    m = re.search(r'<p class="no_today">\s*<em[^>]*>\s*<span[^>]*>([^<]+)</span>', html)
    if m:
        result["price_fallback"] = m.group(1).strip().replace(",", "")
 
    return result
 
 
# ── 누적 히스토리 저장 ──────────────────────────────────────────
HISTORY_PATH = "data/history.json"
HISTORY_MAX_POINTS = 120  # 종목당 최근 약 120영업일(약 6개월) 보관
 
 
def update_history(results: list, date_str: str) -> None:
    """종목별 일별 스냅샷(가격·NAV)을 data/history.json 에 누적 저장"""
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {"series": {}}
 
    series = history.setdefault("series", {})
 
    for e in results:
        if not e.get("fetch_ok"):
            continue
        arr = series.setdefault(e["id"], [])
        # 같은 날짜 중복 저장 방지 (하루 여러 번 돌려도 마지막 값으로 갱신)
        if arr and arr[-1].get("d") == date_str:
            arr[-1] = {"d": date_str, "p": e.get("price", ""), "n": e.get("nav", "")}
        else:
            arr.append({"d": date_str, "p": e.get("price", ""), "n": e.get("nav", "")})
        if len(arr) > HISTORY_MAX_POINTS:
            series[e["id"]] = arr[-HISTORY_MAX_POINTS:]
 
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
 
 
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
 
    # 전체 ETF 목록 API — 1회 호출로 현재가/NAV/순자산 모두 수집
    api_map = fetch_etf_list_api()
    print(f"  API 수집: {len(api_map)}개 종목 정보 확보")
 
    results = []
 
    for etf in ETF_LIST:
        code = etf["code"]
        name = etf["name"]
        print(f"\n  [{code}] {name}")
 
        # 기존 데이터 (수동 입력 PER·PBR 보존)
        prev = existing_map.get(etf["id"], {})
 
        fetched = dict(api_map.get(code, {}))
 
        # API에 없거나 가격이 비어있으면 개별 페이지에서 폴백 시도
        if not fetched.get("price"):
            fallback = fetch_naver_w52(code)
            if fallback.get("price_fallback"):
                fetched["price"] = fallback["price_fallback"]
            fetched.setdefault("w52_high", fallback.get("w52_high", ""))
            fetched.setdefault("w52_low", fallback.get("w52_low", ""))
        else:
            # 가격은 이미 확보됐으니 52주 고저만 보조 수집
            fallback = fetch_naver_w52(code)
            fetched["w52_high"] = fallback.get("w52_high", "")
            fetched["w52_low"] = fallback.get("w52_low", "")
 
        if fetched.get("price"):
            print(f"    현재가: {fetched['price']}원  NAV: {fetched.get('nav','?')}  등락: {fetched.get('chg','?')}%")
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
 
        time.sleep(0.5)   # 네이버 서버 부하 방지
 
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
 
    # 누적 히스토리 저장 (NAV/가격 추이용)
    date_str = datetime.now(kst).strftime("%Y-%m-%d")
    update_history(results, date_str)
 
    print(f"\n{'='*50}")
    print(f"완료: {output['success']}/{output['total']}개 수집 성공")
    print(f"저장: data/etf_data.json, {HISTORY_PATH}")
    print(f"{'='*50}\n")
 
 
if __name__ == "__main__":
    main()
