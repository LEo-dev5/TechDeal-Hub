"""
펨코(FMKorea) 핫딜 게시판 크롤러
대상: https://www.fmkorea.com/hotdeal
"""
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.fmkorea.com"
LIST_URL = f"{BASE_URL}/hotdeal"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.fmkorea.com/",
}

SOLD_OUT_KEYWORDS = ["[종료]", "[품절]", "품절", "마감", "sold out"]

TECH_KEYWORDS = [
    "노트북", "맥북", "모니터", "그래픽카드", "gpu", "rtx", "gtx",
    "cpu", "ryzen", "intel", "ssd", "nvme", "ddr", "ram", "메모리",
    "스마트폰", "아이폰", "갤럭시", "아이패드", "이어폰", "헤드폰",
    "키보드", "마우스", "nas", "공유기", "카메라", "tv", "oled",
    "에어팟", "청소기", "스피커", "태블릿", "충전기", "충전", "케이블",
    "허브", "블루투스", "배터리", "보조배터리", "usb", "hdmi",
    "게이밍", "gaming", "조이스틱", "케이스", "apple", "samsung",
    "애플", "삼성", "lg전자", "가전", "전자", "컴퓨터", "pc",
    "맥세이프", "qi", "무선충전", "airpods", "galaxy", "iphone",
]

# 펨코 전자제품 카테고리 ID 목록 (가전, 컴퓨터 등)
TECH_CATEGORIES = ["가전제품", "컴퓨터", "디지털", "게임", "스마트폰", "모바일"]


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
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else None


def is_tech_deal(title: str, category: str = "") -> bool:
    title_lower = title.lower()
    if any(kw in category for kw in TECH_CATEGORIES):
        return True
    return any(kw in title_lower for kw in TECH_KEYWORDS)


def is_sold_out(title: str) -> bool:
    return any(kw in title.lower() for kw in SOLD_OUT_KEYWORDS)


def fetch_list_page(page: int = 1, delay: float = 3.0) -> list[RawDeal]:
    if delay > 0:
        time.sleep(delay + random.uniform(0, 2))

    url = f"{LIST_URL}?page={page}"

    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"[펨코] HTTP 오류: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    deals: list[RawDeal] = []

    # li[class*="hotdeal"] 로 핫딜 행 선택
    rows = soup.select("li[class*='hotdeal']")
    for row in rows:
        try:
            # 제목: h3.title > a.hotdeal_var* > span.ellipsis-target
            title_a = row.select_one("h3.title a[class*='hotdeal_var']")
            if not title_a:
                continue

            title_span = title_a.select_one("span.ellipsis-target")
            title = title_span.get_text(strip=True) if title_span else title_a.get_text(strip=True)
            if not title:
                continue

            # 카테고리
            category_el = row.select_one("span.category a")
            category = category_el.get_text(strip=True) if category_el else ""

            if not is_tech_deal(title, category):
                continue

            # URL / 게시글 ID
            href = title_a.get("href", "")
            post_id_match = re.search(r"/(\d+)", href)
            if not post_id_match:
                continue
            post_id = post_id_match.group(1)
            source_url = BASE_URL + href if href.startswith("/") else href

            # 가격
            price_a = row.select_one("div.hotdeal_info span a.strong")
            price = None
            if price_a:
                # "가격:" 텍스트 옆 링크
                info_spans = row.select("div.hotdeal_info span")
                for span in info_spans:
                    if "가격" in span.get_text():
                        price = parse_price(span.get_text())
                        break

            # 추천수
            upvote_span = row.select_one("a.pc_voted_count span.count")
            upvotes = 0
            if upvote_span:
                upvote_text = re.sub(r"[^\d]", "", upvote_span.get_text())
                upvotes = int(upvote_text) if upvote_text else 0

            # 댓글수: span.comment_count "[7]"
            comment_span = row.select_one("span.comment_count")
            comments_count = 0
            if comment_span:
                c_text = re.sub(r"[^\d]", "", comment_span.get_text())
                comments_count = int(c_text) if c_text else 0

            # 날짜: span.regdate (당일은 "13:41", 이전은 "02.27")
            date_span = row.select_one("span.regdate")
            posted_at = datetime.now()
            if date_span:
                dt_text = date_span.get_text(strip=True)
                if ":" in dt_text:  # 오늘 시간만 표시
                    try:
                        t = datetime.strptime(dt_text, "%H:%M")
                        posted_at = datetime.now().replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                    except ValueError:
                        pass
                else:  # 날짜 표시 (02.27)
                    for fmt in ("%y.%m.%d", "%Y.%m.%d"):
                        try:
                            posted_at = datetime.strptime(dt_text, fmt)
                            break
                        except ValueError:
                            continue

            # 썸네일
            thumb_span = row.select_one("span.thumb")
            thumbnail_url = None
            if thumb_span:
                style = thumb_span.get("style", "")
                url_match = re.search(r"url\(['\"]?(https?://[^'\")\s]+)", style)
                if url_match:
                    thumbnail_url = url_match.group(1)

            deals.append(RawDeal(
                source_post_id=post_id,
                title=title,
                source_url=source_url,
                mall_url=None,
                price=price,
                upvotes=upvotes,
                comments_count=comments_count,
                posted_at=posted_at,
                thumbnail_url=thumbnail_url,
                is_active=not is_sold_out(title),
            ))

        except Exception as e:
            print(f"[펨코] 파싱 오류: {e}")
            continue

    print(f"[펨코] 페이지 {page}: {len(deals)}개 전자제품 핫딜 수집")
    return deals


def crawl(pages: int = 3) -> list[RawDeal]:
    all_deals: list[RawDeal] = []
    for page in range(1, pages + 1):
        all_deals.extend(fetch_list_page(page=page, delay=3.0))
    return all_deals
