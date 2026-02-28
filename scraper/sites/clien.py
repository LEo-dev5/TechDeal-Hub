"""
클리앙 핫딜 게시판 크롤러
대상: https://www.clien.net/service/board/jiankr
"""
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.clien.net"
LIST_URL = f"{BASE_URL}/service/board/jirum"

HEADERS = {
    "User-Agent": "TechDealBot/1.0 (+https://github.com/LEo-dev5/TechDeal-Hub)",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SOLD_OUT_KEYWORDS = ["[종료]", "[품절]", "품절", "마감", "sold out"]

TECH_KEYWORDS = [
    # 기기
    "노트북", "맥북", "모니터", "그래픽카드", "gpu", "rtx", "gtx",
    "cpu", "ryzen", "intel", "ssd", "nvme", "ddr", "ram", "메모리",
    "스마트폰", "아이폰", "갤럭시", "아이패드", "이어폰", "헤드폰",
    "키보드", "마우스", "nas", "공유기", "카메라", "tv", "oled",
    "에어팟", "청소기", "스피커", "태블릿", "케이스", "충전기", "충전",
    # 앱/소프트웨어 (클리앙 jirum 특성)
    "ios", "android", "wearos", "애플", "apple", "samsung", "구글", "google",
    "앱", "app", "게임", "game", "무료", "할인", "맥세이프", "magsafe",
    "qi2", "qi ", "usb", "hdmi", "dp ", "블루투스", "bluetooth", "wifi",
    "airpods", "galaxy", "iphone", "ipad", "macbook", "watch",
    # 액세서리
    "케이블", "허브", "어댑터", "배터리", "보조배터리", "파워뱅크",
    "거치대", "스탠드", "웹캠", "마이크", "스트리밍", "조이스틱",
]


@dataclass
class RawDeal:
    source_post_id: str
    title: str
    source_url: str
    mall_url: Optional[str]
    price: Optional[int]
    upvotes: int
    comments_count: int
    posted_at: datetime
    thumbnail_url: Optional[str] = None
    is_active: bool = True


def is_tech_deal(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in TECH_KEYWORDS)


def is_sold_out(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in SOLD_OUT_KEYWORDS)


def parse_price(text: str) -> Optional[int]:
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else None


def fetch_list_page(page: int = 0, delay: float = 3.0) -> list[RawDeal]:
    """
    클리앙 알뜰구매 목록 크롤링

    Args:
        page: 페이지 번호 (0부터 시작)
        delay: 요청 전 대기 시간(초)
    """
    if delay > 0:
        time.sleep(delay + random.uniform(0, 2))

    url = f"{LIST_URL}?po={page}"

    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"[클리앙] HTTP 오류: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    deals: list[RawDeal] = []

    # 실제 HTML: div.list_item.jirum (공지/홍보 제외)
    rows = soup.select("div.list_item.jirum")
    for row in rows:
        try:
            # 제목: div.list_title > span.list_subject > a
            title_a = row.select_one("div.list_title span.list_subject a")
            if not title_a:
                continue

            title = title_a.get_text(strip=True)
            if not title or not is_tech_deal(title):
                continue

            href = title_a.get("href", "")
            post_id_match = re.search(r"/(\d+)$", href)
            if not post_id_match:
                continue
            post_id = post_id_match.group(1)
            source_url = BASE_URL + href if href.startswith("/") else href

            # 댓글수 (클리앙 jirum 목록에는 댓글수 없음)
            comments_count = 0

            # 날짜: div.list_time > span.time > span.timestamp
            date_span = row.select_one("span.timestamp")
            posted_at = datetime.now()
            if date_span:
                dt_text = date_span.get_text(strip=True)
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        posted_at = datetime.strptime(dt_text, fmt)
                        break
                    except ValueError:
                        continue

            # 조회수 (좋아요 대신)
            hit_span = row.select_one("div.list_hit span.hit")
            upvotes = 0
            if hit_span:
                hit_text = hit_span.get_text(strip=True).replace(",", "").replace(".", "").replace(" ", "")
                # "26.3 k" 형태 처리
                if "k" in hit_text.lower():
                    num = re.sub(r"[^\d]", "", hit_text)
                    upvotes = int(num) * 100 if num else 0
                else:
                    num = re.sub(r"[^\d]", "", hit_text)
                    upvotes = int(num) if num else 0

            # 썸네일
            thumb_img = row.select_one("div.list_image img")
            thumbnail_url = None
            if thumb_img:
                src = thumb_img.get("src", "")
                if src and "noimage" not in src:
                    thumbnail_url = src

            deals.append(RawDeal(
                source_post_id=post_id,
                title=title,
                source_url=source_url,
                mall_url=None,
                price=None,
                upvotes=upvotes,
                comments_count=comments_count,
                posted_at=posted_at,
                thumbnail_url=thumbnail_url,
                is_active=not is_sold_out(title),
            ))

        except Exception as e:
            print(f"[클리앙] 파싱 오류: {e}")
            continue

    print(f"[클리앙] 페이지 {page}: {len(deals)}개 전자제품 핫딜 수집")
    return deals


def crawl(pages: int = 3) -> list[RawDeal]:
    all_deals: list[RawDeal] = []
    for page in range(pages):
        page_deals = fetch_list_page(page=page, delay=3.0)
        all_deals.extend(page_deals)
    return all_deals
