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
    except Exception as e:
        print(f"  [오류] ETF 목록 API 호출 실패: {type(e).__name__}: {e}")
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
    except Exception as e:
        print(f"  [오류] {code} 52주 정보: {type(e).__name__}: {e}")
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

        try:
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
        except Exception as e:
            # 종목 하나에서 예외가 나도 전체 실행은 계속 진행 — 이전 데이터로 대체
            print(f"    ⚠ [예외] {code} 처리 중 오류: {type(e).__name__}: {e}")
            prev = existing_map.get(etf["id"], {})
            entry = {
                **etf,
                "price": prev.get("price", ""), "chg": prev.get("chg", ""),
                "chg_dir": prev.get("chg_dir", "flat"), "nav": prev.get("nav", ""),
                "aum": prev.get("aum", ""), "w52_high": prev.get("w52_high", ""),
                "w52_low": prev.get("w52_low", ""), "per": prev.get("per", ""),
                "pbr": prev.get("pbr", ""), "updated": now_str, "fetch_ok": False,
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
    try:
        main()
    except Exception as e:
        import traceback
        print("\n[치명적 오류] crawl.py 실행 중 예외 발생:")
        traceback.print_exc()
        # 부분 데이터라도 있으면 그대로 두고, 다음 실행에서 재시도되도록 exit 0으로 종료
        # (여기서 exit 1로 죽으면 GitHub Actions에서 이후 배포 단계까지 막힘)
        raise SystemExit(0)
