
Claude가 응답을 완료했습니다

포트폴리오 대시보드 구조를 설계하고 핵심 지표를 배치했다
포트폴리오 대시보드 구조를 설계하고 핵심 지표를 배치했다
좋은 구성이네요. 정리하면 이렇게 반영하겠습니다.

최상단 요약 영역 (새로 추가)

┌─────────────────────────────────────┐
│  현재 보유금액        전일대비          │
│  12,450,000원        ▲ +85,000 (+0.7%) │
│                                       │
│  금월 예상 분배금                       │
│  98,500원                             │
└─────────────────────────────────────┘
현재 보유금액: 보유수량 × 현재가 합계
전일대비: 각 종목의 당일 등락률 × 평가금액을 합산해서 금액(원)과 %로 표시 (지금 있는 계산 방식 그대로 재사용)
금월 예상 분배금: 종목별 (보유수량 × 현재가 × 월배당율%) 을 합산 — 월배당율을 입력하시면 이 값 기준으로 계산됩니다
보내주실 데이터 양식 (메모장/CSV 형태로 편하실 대로)

종목명, 수량, 평균매입가, 월배당율(%)
KODEX 200, 50, 38500, 0
KODEX 미국배당커버드콜액티브, 120, 10200, 0.9
월배당율은 "월 기준" 분배율(%)로 부탁드립니다 (예: 연 10.8% 상품이면 월 0.9% 식으로)
배당이 없는 종목(KODEX 200 등 일반 지수형)은 0 또는 비워두시면 됩니다
이 데이터 주시면:

crawl.py 종목 목록을 보유종목만 남기도록 정리
data/holdings.csv(또는 index.html 안에 직접 내장) 형태로 반영
index.html 최상단에 위 요약 박스 추가 + 기존 카드형 목록은 보유종목만 표시
데이터 정리되시면 채팅으로 올려주세요, 바로 작업 들어가겠습니다.

여러 계좌에 정보가 나눠져 있어서 동일한 종목이 반복될 수도 있는데 합쳐서 평균으로 넣어줄 수 있겠느냐? 예를 들어 A 계좌에 100주 만원, B 계좌 150주 이만원에 동일 종목을 샀는데 합쳐서 써주기 힘들어서 그런데 둘을 합쳐서 평균 매입가랑 보유 주식량은 단순히 합치면 되겠다.

네, 그렇게 하시는 게 훨씬 편합니다. 계좌별로 나눠서 그대로 주시면 제가(정확히는 홈페이지 코드가) 자동으로 합쳐드릴게요. 수동으로 평균 낼 필요 없습니다.

합산 방식: 같은 종목이 여러 줄 나오면 자동으로

수량 = 단순 합산
평균매입가 = 가중평균 (수량×매입가의 합 ÷ 수량의 합)
으로 계산하도록 만들겠습니다. 예시로 주신 경우:

A계좌 100주 @ 10,000원
B계좌 150주 @ 20,000원
→ 합산: 250주, 평균매입가 = (100×10,000 + 150×20,000) / 250 = 16,000원
데이터는 계좌 구분 없이 그냥 종목별로 여러 줄 나열해서 주시면 됩니다:

종목명, 수량, 매입가, 월배당율(%)
KODEX 200, 100, 10000, 0
KODEX 200, 150, 20000, 0
KODEX 미국배당커버드콜액티브, 80, 10500, 0.9
KODEX 미국배당커버드콜액티브, 40, 9800, 0.9
(월배당율은 종목당 한 번만 적어주셔도 되고, 매 줄 반복 적어주셔도 상관없습니다)

이 형태로 정리해서 올려주세요. 받는 대로 자동 합산 로직까지 포함해서 반영하겠습니다.

종목명, 종목코드, 매입가, 월배당율(%)
KODEX 미국AI광통신네트워크, 0173Y0, 8, 14969, 0%
KODEX 200, 069500, 104, 83908, 0%
KODEX 미국빅테크10(H), 314250, 158, 60620, 0%
TIGER 반도체 TOP10, 396500, 151, 40229, 0%
SOL AI반도체TOP2플러스, 0167A0, 294, 26695, 0%
KODEX 200, 069500, 106, 84571, 0%
KODEX 코스닥150, 229200, 240, 19587, 0%
TIGER 미국S&P500, 360750, 493, 25712, 0%
 TIGER 반도체 TOP10, 396500, 429, 44081, 0%
KODEX 미국배당커버드콜액티브, 441640, 920, 13207, 0.73%
TIGER 미국배당다우존스, 458730, 1273, 15055, 0.23%
KODEX 한국부동산리츠인프라, 476800, 1488, 4436, 0.72%
KODEX 미국나스닥100데일리커버드콜OTM, 494300, 3369, 10496, 1.66%
KODEX 200타겟위클리커버드콜, 498400, 1741, 21486, 1.14%
KODEX 금융고배당TOP10타켓위클리커버드콜, 498410, 1763, 12911, 1.26%
KODEX 200커버드콜액티브, 0219E0, 140, 8960, 0%
KODEX 200타겟위클리커버드콜, 498400, 886, 22084, 1.14%
KODEX 미국나스닥100데일리커버드콜OTM, 494300, 1044, 10855, 1.66%
RISE 현대차고정피지컬AI, 0190C0, 293, 12555, 0%
KODEX 미국배당커버드콜액티브, 441640, 1229, 13200, 0.73%
KODEX 금융고배당TOP10타켓위클리커버드콜, 498410, 495, 12625, 1.26%
KODEX 미국30년국채타겟커버드콜(합성H), 481060, 540, 7560, 1.1%
KODEX 미국AI테크TOP10타겟커버드콜, 483280, 383, 12825, 1.2%
KODEX 미국나스닥100데일리커버드콜OTM, 494300, 539, 10135, 1.66%

위의 종목으로 만들고 지금 홈페이지와 내 핸드폰에서도 동일한 정보를 보고 싶다. 그대로 종목정보도 넘어갈 수 있게 해주고 ETF 분류는 크게 미국지수, 미국배당, 한국지수, 한국배당 4개 카테고리로 정리하자

더 보기

포트폴리오 통합 후 네 카테고리로 재구성하고 하드코딩했다
포트폴리오 통합 후 네 카테고리로 재구성하고 하드코딩했다
좋습니다. 계좌 합산과 4개 카테고리 분류까지 반영해서 처음부터 다시 정리하�n. 먼저 종목별 수량을 합산한 계산 결과부터 보여드릴게요.


명령 2개 실행함
명령 2개 실행함
이제 전체 파일을 새로 정리하겠습니다.


Rewrite crawl.py with holdings-only list and 4 categories
Rewrite crawl.py with holdings-only list and 4 categories
이제 index.html도 새 카테고리 체계 + 상단 요약(보유금액/전일대비/금월분배금)으로 다시 작성하겠습니다.


명령 2개 실행함, 파일 읽음
명령 2개 실행함, 파일 읽음
정리 내용

1. 계좌 합산 — 같은 종목을 여러 계좌 걸쳐 매입하신 경우, 수량은 단순합산 / 매입가는 수량가중평균으로 자동 계산해서 17개 보유종목으로 정리했습니다. (예: KODEX 200은 104주@83,908원 + 106주@84,571원 → 210주@평균 84,243원)

2. 4개 카테고리로 재분류

🇰🇷 한국지수: KODEX 200, TIGER 반도체TOP10, SOL AI반도체TOP2+, KODEX 코스닥150, RISE 현대차고정피지컬AI
🇰🇷 한국배당: KODEX 한국부동산리츠인프라, KODEX 200타겟위클리커버드콜, KODEX 금융고배당TOP10타겟위클리커버드콜, KODEX 200커버드콜액티브
🇺🇸 미국지수: KODEX 미국AI광통신네트워크, KODEX 미국빅테크10(H), TIGER 미국S&P500
🇺🇸 미국배당: KODEX 미국배당커버드콜액티브, TIGER 미국배당다우존스, KODEX 미국나스닥100데일리커버드콜OTM, KODEX 미국30년국채타겟커버드콜(합성H), KODEX 미국AI테크TOP10타겟커버드콜
3. 데이터를 서버(저장소)에 직접 저장하는 방식으로 전환
지난번엔 브라우저별 localStorage 방식이라 기기마다 따로 입력해야 했는데, 이번엔 보유수량·매입가·월배당율을 crawl.py 안에 직접 넣어서 GitHub Actions가 계산·저장하도록 바꿨습니다. → PC, 휴대폰 어디서 접속하든 동일한 정보가 보입니다.

4. 화면 최상단에 요청하신 요약 박스 추가

현재 보유금액 (전체 평가금액)
전일대비 등락 (금액 + %, 우측에 표시)
이번달 예상 분배금 (보유수량 × 현재가 × 월배당율%로 자동계산)
적용 방법

crawl.py, index.html 두 파일을 GitHub에서 기존 내용 전체 삭제 후 새 내용으로 교체 → 커밋
Actions 탭 → Run workflow로 수동 1회 실행
완료되면 사이트 새로고침 (PC든 휴대폰이든 동일하게 보입니다)
참고: 나중에 매수/매도로 수량이나 평균가가 바뀌면, crawl.py의 ETF_LIST 안 숫자만 알려주시면 제가 반영해드리겠습니다.


Crawl
PY 

Index
코드 · HTML 

Claude가 응답할 때 알림을 받으시겠습니까?





Claude는 AI이며 실수할 수 있습니다. 응답을 다시 한번 확인해 주세요.
Crawl · PY
"""
ETF 모니터 — 네이버금융 자동 수집 스크립트
평일 16:00(KST) GitHub Actions에서 자동 실행됩니다.
 
보유 종목만 관리합니다. 종목별 보유수량(qty)·평균매입가(avg_price)·월배당율(myield %)은
여러 계좌의 보유분을 합산(가중평균)한 값이 미리 계산되어 아래 ETF_LIST에 들어있습니다.
계좌 변동(추가매수/매도 등)이 있으면 이 리스트의 숫자만 갱신하면 됩니다.
"""
 
import json
import time
import re
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError
 
# ── 보유 ETF 목록 (계좌 합산 완료) ────────────────────────────
# cat: kr_idx(한국지수) / kr_div(한국배당) / us_idx(미국지수) / us_div(미국배당)
ETF_LIST = [
    {"id": "e01", "code": "069500", "name": "KODEX 200",                              "cat": "kr_idx", "qty": 210,  "avg_price": 84243, "myield": 0.0},
    {"id": "e02", "code": "396500", "name": "TIGER 반도체TOP10",                       "cat": "kr_idx", "qty": 580,  "avg_price": 43078, "myield": 0.0},
    {"id": "e03", "code": "0167A0", "name": "SOL AI반도체TOP2플러스",                   "cat": "kr_idx", "qty": 294,  "avg_price": 26695, "myield": 0.0},
    {"id": "e04", "code": "229200", "name": "KODEX 코스닥150",                          "cat": "kr_idx", "qty": 240,  "avg_price": 19587, "myield": 0.0},
    {"id": "e05", "code": "0190C0", "name": "RISE 현대차고정피지컬AI",                  "cat": "kr_idx", "qty": 293,  "avg_price": 12555, "myield": 0.0},
 
    {"id": "e06", "code": "476800", "name": "KODEX 한국부동산리츠인프라",               "cat": "kr_div", "qty": 1488, "avg_price": 4436,  "myield": 0.72},
    {"id": "e07", "code": "498400", "name": "KODEX 200타겟위클리커버드콜",              "cat": "kr_div", "qty": 2627, "avg_price": 21688, "myield": 1.14},
    {"id": "e08", "code": "498410", "name": "KODEX 금융고배당TOP10타겟위클리커버드콜", "cat": "kr_div", "qty": 2258, "avg_price": 12848, "myield": 1.26},
    {"id": "e09", "code": "0219E0", "name": "KODEX 200커버드콜액티브",                  "cat": "kr_div", "qty": 140,  "avg_price": 8960,  "myield": 0.0},
 
    {"id": "e10", "code": "0173Y0", "name": "KODEX 미국AI광통신네트워크",              "cat": "us_idx", "qty": 8,    "avg_price": 14969, "myield": 0.0},
    {"id": "e11", "code": "314250", "name": "KODEX 미국빅테크10(H)",                   "cat": "us_idx", "qty": 158,  "avg_price": 60620, "myield": 0.0},
    {"id": "e12", "code": "360750", "name": "TIGER 미국S&P500",                        "cat": "us_idx", "qty": 493,  "avg_price": 25712, "myield": 0.0},
 
    {"id": "e13", "code": "441640", "name": "KODEX 미국배당커버드콜액티브",             "cat": "us_div", "qty": 2149, "avg_price": 13203, "myield": 0.73},
    {"id": "e14", "code": "458730", "name": "TIGER 미국배당다우존스",                  "cat": "us_div", "qty": 1273, "avg_price": 15055, "myield": 0.23},
    {"id": "e15", "code": "494300", "name": "KODEX 미국나스닥100데일리커버드콜OTM",    "cat": "us_div", "qty": 4952, "avg_price": 10532, "myield": 1.66},
    {"id": "e16", "code": "481060", "name": "KODEX 미국30년국채타겟커버드콜(합성H)",   "cat": "us_div", "qty": 540,  "avg_price": 7560,  "myield": 1.1},
    {"id": "e17", "code": "483280", "name": "KODEX 미국AI테크TOP10타겟커버드콜",       "cat": "us_div", "qty": 383,  "avg_price": 12825, "myield": 1.2},
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
 
        prev = existing_map.get(etf["id"], {})
        fetched = dict(api_map.get(code, {}))
 
        if not fetched.get("price"):
            fallback = fetch_naver_w52(code)
            if fallback.get("price_fallback"):
                fetched["price"] = fallback["price_fallback"]
            fetched.setdefault("w52_high", fallback.get("w52_high", ""))
            fetched.setdefault("w52_low", fallback.get("w52_low", ""))
        else:
            fallback = fetch_naver_w52(code)
            fetched["w52_high"] = fallback.get("w52_high", "")
            fetched["w52_low"] = fallback.get("w52_low", "")
 
        if fetched.get("price"):
            print(f"    현재가: {fetched['price']}원  NAV: {fetched.get('nav','?')}  등락: {fetched.get('chg','?')}%")
        else:
            print(f"    ⚠ 가격 수집 실패 — 이전 값 유지")
 
        entry = {
            **etf,   # id, code, name, cat, qty, avg_price, myield 그대로 포함
            "price":    fetched.get("price")    or prev.get("price", ""),
            "chg":      fetched.get("chg")      or prev.get("chg", ""),
            "chg_dir":  fetched.get("chg_dir")  or prev.get("chg_dir", "flat"),
            "nav":      fetched.get("nav")       or prev.get("nav", ""),
            "aum":      fetched.get("aum")       or prev.get("aum", ""),
            "w52_high": fetched.get("w52_high")  or prev.get("w52_high", ""),
            "w52_low":  fetched.get("w52_low")   or prev.get("w52_low", ""),
            "per":      prev.get("per", ""),   # 수동 보존
            "pbr":      prev.get("pbr", ""),   # 수동 보존
            "updated":  now_str,
            "fetch_ok": bool(fetched.get("price")),
        }
        results.append(entry)
 
        time.sleep(0.5)   # 네이버 서버 부하 방지
 
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
 
    date_str = datetime.now(kst).strftime("%Y-%m-%d")
    update_history(results, date_str)
 
    print(f"\n{'='*50}")
    print(f"완료: {output['success']}/{output['total']}개 수집 성공")
    print(f"저장: data/etf_data.json, {HISTORY_PATH}")
    print(f"{'='*50}\n")
 
 
if __name__ == "__main__":
    main()
 
