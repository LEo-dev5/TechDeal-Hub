"""
퀘이사존 세일정보 게시판 크롤러
대상: https://quasarzone.com/bbs/qb_saleinfo
"""
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://quasarzone.com"
LIST_URL = f"{BASE_URL}/bbs/qb_saleinfo"

HEADERS = {
    "User-Agent": "TechDealBot/1.0 (+https://github.com/LEo-dev5/TechDeal-Hub)",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://quasarzone.com/",
}

SOLD_OUT_KEYWORDS = ["종료", "품절", "마감", "sold out"]

TECH_KEYWORDS = [
    "노트북", "맥북", "모니터", "그래픽카드", "gpu", "rtx", "gtx",
    "cpu", "ryzen", "intel", "ssd", "nvme", "ddr", "ram", "메모리",
    "스마트폰", "아이폰", "갤럭시", "아이패드", "이어폰", "헤드폰",
    "키보드", "마우스", "nas", "공유기", "카메라", "tv", "oled",
    "에어팟", "청소기", "스피커", "태블릿", "충전기", "충전", "케이블",
    "허브", "블루투스", "배터리", "보조배터리", "usb", "hdmi",
    "게이밍", "gaming", "케이스", "apple", "samsung", "lg",
    "애플", "삼성", "가전", "전자", "컴퓨터", "pc", "맥세이프",
    "airpods", "galaxy", "iphone", "ipad", "macbook", "watch",
    "qi", "무선충전", "어댑터", "웹캠", "마이크",
]

TECH_CATEGORIES = ["PC부품", "노트북", "모니터", "주변기기", "스마트기기", "가전", "디지털"]


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


def parse_price(text: str) -> Optional[int]:
    # "￦ 9,900 (KRW)" → 9900
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else None


def parse_relative_date(text: str) -> datetime:
    """
    퀘이사존 날짜 포맷 파싱
    '2시간 전', '30분 전', '2026.02.28' 등
    """
    now = datetime.now()
    text = text.strip()

    if "분 전" in text:
        mins = int(re.search(r"(\d+)", text).group(1))
        return now - timedelta(minutes=mins)
    if "시간 전" in text:
        hours = int(re.search(r"(\d+)", text).group(1))
        return now - timedelta(hours=hours)
    if "일 전" in text:
        days = int(re.search(r"(\d+)", text).group(1))
        return now - timedelta(days=days)

    for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return now


def is_tech_deal(title: str, category: str = "") -> bool:
    if any(kw in category for kw in TECH_CATEGORIES):
        return True
    return any(kw in title.lower() for kw in TECH_KEYWORDS)


def is_sold_out(label: str) -> bool:
    return any(kw in label for kw in SOLD_OUT_KEYWORDS)


def fetch_list_page(page: int = 1, delay: float = 3.0) -> list[RawDeal]:
    if delay > 0:
        time.sleep(delay + random.uniform(0, 2))

    url = f"{LIST_URL}?page={page}"

    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"[퀘이사존] HTTP 오류: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    deals: list[RawDeal] = []

    items = soup.select("div.market-info-list")
    for item in items:
        try:
            # 제목
            title_a = item.select_one("a.subject-link")
            if not title_a:
                continue
            title_span = title_a.select_one("span.ellipsis-with-reply-cnt")
            title = title_span.get_text(strip=True) if title_span else title_a.get_text(strip=True)
            if not title:
                continue

            # 카테고리
            category_el = item.select_one("span.category")
            category = category_el.get_text(strip=True) if category_el else ""

            if not is_tech_deal(title, category):
                continue

            # URL / 게시글 ID
            href = title_a.get("href", "")
            post_id_match = re.search(r"/views/(\d+)", href)
            if not post_id_match:
                continue
            post_id = post_id_match.group(1)
            source_url = BASE_URL + href if href.startswith("/") else href

            # 가격
            price_span = item.select_one("span.text-orange")
            price = parse_price(price_span.get_text()) if price_span else None

            # 진행중/종료 상태
            label_span = item.select_one("p.tit span.label")
            label_text = label_span.get_text(strip=True) if label_span else ""
            active = not is_sold_out(label_text)

            # 조회수
            count_span = item.select_one("span.count")
            upvotes = 0
            if count_span:
                c_text = re.sub(r"[^\d]", "", count_span.get_text())
                upvotes = int(c_text) if c_text else 0

            # 날짜
            date_span = item.select_one("span.date")
            posted_at = datetime.now()
            if date_span:
                posted_at = parse_relative_date(date_span.get_text(strip=True))

            # 썸네일
            thumb_img = item.select_one("div.thumb-wrap img.maxImg")
            thumbnail_url = None
            if thumb_img:
                src = thumb_img.get("src", "")
                if src and "quasarzone" in src:
                    thumbnail_url = src

            deals.append(RawDeal(
                source_post_id=post_id,
                title=title,
                source_url=source_url,
                mall_url=None,
                price=price,
                upvotes=upvotes,
                comments_count=0,
                posted_at=posted_at,
                thumbnail_url=thumbnail_url,
                is_active=active,
            ))

        except Exception as e:
            print(f"[퀘이사존] 파싱 오류: {e}")
            continue

    print(f"[퀘이사존] 페이지 {page}: {len(deals)}개 전자제품 핫딜 수집")
    return deals


def crawl(pages: int = 3) -> list[RawDeal]:
    all_deals: list[RawDeal] = []
    for page in range(1, pages + 1):
        all_deals.extend(fetch_list_page(page=page, delay=3.0))
    return all_deals
