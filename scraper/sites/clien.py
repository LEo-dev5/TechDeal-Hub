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
LIST_URL = f"{BASE_URL}/service/board/jiankr"

HEADERS = {
    "User-Agent": "TechDealBot/1.0 (+https://github.com/LEo-dev5/TechDeal-Hub)",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SOLD_OUT_KEYWORDS = ["[종료]", "[품절]", "품절", "마감", "sold out"]

TECH_KEYWORDS = [
    "노트북", "맥북", "모니터", "그래픽카드", "gpu", "rtx", "gtx",
    "cpu", "ryzen", "intel", "ssd", "nvme", "ddr", "ram", "메모리",
    "스마트폰", "아이폰", "갤럭시", "아이패드", "이어폰", "헤드폰",
    "키보드", "마우스", "nas", "공유기", "카메라", "tv", "oled",
    "에어팟", "청소기", "스피커", "태블릿",
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

    rows = soup.select("div.list_item.symph_row")
    for row in rows:
        try:
            # 공지글 스킵
            if row.select_one("span.notice_tag"):
                continue

            title_a = row.select_one("span.subject_fixed a.list_subject")
            if not title_a:
                title_a = row.select_one("a.list_subject")
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

            # 댓글수
            reply_span = row.select_one("span.reply_symph")
            comments_count = 0
            if reply_span:
                c_text = re.sub(r"[^\d]", "", reply_span.get_text())
                comments_count = int(c_text) if c_text else 0

            # 날짜
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

            # 좋아요
            like_span = row.select_one("span.symph_count")
            upvotes = 0
            if like_span:
                like_text = re.sub(r"[^\d]", "", like_span.get_text())
                upvotes = int(like_text) if like_text else 0

            deals.append(RawDeal(
                source_post_id=post_id,
                title=title,
                source_url=source_url,
                mall_url=None,
                price=None,
                upvotes=upvotes,
                comments_count=comments_count,
                posted_at=posted_at,
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
