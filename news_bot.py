"""
보유 ETF 관련 뉴스를 매일 아침 수집해 카카오톡으로 전송하는 스크립트.

데이터 흐름:
1. etf-monitor 저장소의 data/etf_data.json에서 현재 보유 종목명 목록을 가져온다.
2. 종목명별로 네이버 뉴스 검색 API + 구글 뉴스 RSS에서 최신 뉴스를 검색한다.
3. 제목 유사도로 중복(같은 사건을 다룬 기사)을 제거하고, 종목당 상위 N건만 남긴다.
4. 카카오 "나에게 보내기" API로 정리된 메시지를 전송한다.

필요한 환경변수 (GitHub Actions Secrets로 주입):
  NAVER_CLIENT_ID       - 네이버 개발자센터에서 발급받은 검색 API Client ID
  NAVER_CLIENT_SECRET   - 위와 짝을 이루는 Client Secret
  KAKAO_REST_API_KEY    - 카카오 개발자센터 앱의 REST API 키
  KAKAO_REFRESH_TOKEN   - 최초 1회 수동으로 발급받은 리프레시 토큰 (get_kakao_token.py 참고)

네이버/구글 중 하나의 키가 없으면 해당 소스는 건너뛰고 나머지 소스만으로 동작한다.
"""

import os
import re
import json
import html
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

ETF_DATA_URL = "https://raw.githubusercontent.com/jongwooson16-max/etf-monitor/main/data/etf_data.json"
SITE_URL = "https://jongwooson16-max.github.io/etf-monitor/"

NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
KAKAO_REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
KAKAO_REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

MAX_NEWS_PER_ETF = 2
SIMILARITY_THRESHOLD = 0.55


def fetch_url(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def get_holdings():
    """etf_data.json에서 보유 종목명 목록을 가져온다."""
    try:
        raw = fetch_url(ETF_DATA_URL)
        data = json.loads(raw.decode("utf-8"))
        names = [etf["name"] for etf in data.get("etfs", []) if etf.get("name")]
        return names
    except Exception as e:
        print(f"[오류] 보유 종목 로드 실패: {e}")
        return []


def strip_tags(text):
    return re.sub("<.*?>", "", html.unescape(text or "")).strip()


def search_naver_news(query, display=5):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return []
    url = "https://openapi.naver.com/v1/search/news.json?" + urllib.parse.urlencode(
        {"query": query, "display": display, "sort": "date"}
    )
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        results = []
        for item in data.get("items", []):
            title = strip_tags(item.get("title", ""))
            link = item.get("originallink") or item.get("link")
            if title and link:
                results.append({"title": title, "link": link, "source": "네이버"})
        return results
    except Exception as e:
        print(f"[네이버 검색 실패] {query}: {e}")
        return []


def search_google_news(query, display=5):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        xml_bytes = fetch_url(url)
        root = ET.fromstring(xml_bytes)
        results = []
        for item in root.findall(".//item")[:display]:
            title = strip_tags(item.findtext("title") or "")
            link = (item.findtext("link") or "").strip()
            if title and link:
                results.append({"title": title, "link": link, "source": "구글"})
        return results
    except Exception as e:
        print(f"[구글 검색 실패] {query}: {e}")
        return []


def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() >= SIMILARITY_THRESHOLD


def dedup(news_list):
    unique = []
    for n in news_list:
        if not any(is_similar(n["title"], u["title"]) for u in unique):
            unique.append(n)
    return unique


def collect_news_for_etf(name):
    combined = dedup(search_naver_news(name) + search_google_news(name))
    return combined[:MAX_NEWS_PER_ETF]


def build_message(news_by_etf):
    today = time.strftime("%Y-%m-%d (%a)")
    lines = [f"📰 {today} 보유 ETF 뉴스 브리핑"]
    has_content = False
    for name, news_list in news_by_etf.items():
        if not news_list:
            continue
        has_content = True
        lines.append(f"\n■ {name}")
        for n in news_list:
            lines.append(f"- [{n['source']}] {n['title']}")
    if not has_content:
        return None
    return "\n".join(lines)


def refresh_kakao_token():
    url = "https://kauth.kakao.com/oauth/token"
    payload = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "client_id": KAKAO_REST_API_KEY,
            "refresh_token": KAKAO_REFRESH_TOKEN,
        }
    ).encode()
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def send_kakao_message(access_token, text):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    # 카카오 텍스트 템플릿은 200자 제한이 있어 넘으면 잘라서 보낸다.
    template = {
        "object_type": "text",
        "text": text[:190] + ("\n…(전체는 사이트 참고)" if len(text) > 190 else ""),
        "link": {"web_url": SITE_URL, "mobile_web_url": SITE_URL},
        "button_title": "포트폴리오 사이트 열기",
    }
    payload = urllib.parse.urlencode({"template_object": json.dumps(template)}).encode()
    req = urllib.request.Request(url, data=payload)
    req.add_header("Authorization", f"Bearer {access_token}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()


def main():
    if not KAKAO_REST_API_KEY or not KAKAO_REFRESH_TOKEN:
        print("[오류] 카카오 인증 정보(KAKAO_REST_API_KEY / KAKAO_REFRESH_TOKEN)가 없습니다.")
        raise SystemExit(1)

    holdings = get_holdings()
    if not holdings:
        print("[중단] 보유 종목을 하나도 가져오지 못했습니다.")
        raise SystemExit(1)

    print(f"보유 종목 {len(holdings)}개 뉴스 수집 시작: {holdings}")
    news_by_etf = {}
    for name in holdings:
        news_by_etf[name] = collect_news_for_etf(name)
        time.sleep(0.3)  # API 과호출 방지

    message = build_message(news_by_etf)
    if not message:
        print("전송할 뉴스가 없어 종료합니다.")
        return

    print("--- 전송할 메시지 미리보기 ---")
    print(message)
    print("-----------------------------")

    token_data = refresh_kakao_token()
    access_token = token_data.get("access_token")
    if not access_token:
        print(f"[오류] 카카오 토큰 갱신 실패: {token_data}")
        raise SystemExit(1)

    send_kakao_message(access_token, message)
    print("카카오톡 전송 완료.")

    # 리프레시 토큰이 갱신되어 새로 발급된 경우, 다음 워크플로우 스텝에서
    # Secrets를 자동 갱신할 수 있도록 GitHub Actions 출력값으로 넘긴다.
    new_refresh_token = token_data.get("refresh_token")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if new_refresh_token and github_output:
        print("::add-mask::" + new_refresh_token)
        with open(github_output, "a") as f:
            f.write(f"new_refresh_token={new_refresh_token}\n")


if __name__ == "__main__":
    main()
