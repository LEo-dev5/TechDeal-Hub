"""
루리웹 핫딜 게시판 크롤러
대상: https://bbs.ruliweb.com/market/board/1020
"""
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://bbs.ruliweb.com"
LIST_URL = f"{BASE_URL}/market/board/1020"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://bbs.ruliweb.com/",
}

SOLD_OUT_KEYWORDS = ["[종료]", "[품절]", "품절", "마감", "sold out"]

TECH_KEYWORDS = [
    "노트북", "맥북", "모니터", "그래픽카드", "gpu", "rtx", "gtx",
    "cpu", "ryzen", "intel", "ssd", "nvme", "ddr", "ram", "메모리",
    "스마트폰", "아이폰", "갤럭시", "아이패드", "이어폰", "헤드폰",
    "키보드", "마우스", "nas", "공유기", "카메라", "tv", "oled",
    "에어팟", "청소기", "스피커", "태블릿", "충전기", "충전", "케이블",
    "허브", "블루투스", "배터리", "보조배터리", "usb", "hdmi",
    "게이밍", "gaming", "케이스", "apple", "samsung", "애플", "삼성",
    "가전", "전자", "컴퓨터", "pc ", "맥세이프", "qi", "무선충전",
    "airpods", "galaxy", "iphone", "ipad", "macbook",
    "조이스틱", "패드", "컨트롤러", "게임기", "닌텐도", "플스", "xbox",
    "무료", "프로모코드", "스팀",
]

TECH_CATEGORIES = ["PC", "노트북", "모니터", "가전", "디지털", "스마트폰", "게임", "주변기기"]


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


def parse_posted_at(text: str) -> datetime:
    """
    루리웹 날짜 파싱
    당일: "10:48", 이전: "2026.02.27"
    """
    text = text.strip()
    now = datetime.now()

    if ":" in text and len(text) == 5:  # "HH:MM"
        try:
            t = datetime.strptime(text, "%H:%M")
            return now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            pass

    for fmt in ("%Y.%m.%d", "%y.%m.%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return now


def is_tech_deal(title: str, category: str = "") -> bool:
    if any(kw in category for kw in TECH_CATEGORIES):
        return True
    return any(kw in title.lower() for kw in TECH_KEYWORDS)


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
        print(f"[루리웹] HTTP 오류: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    deals: list[RawDeal] = []

    rows = soup.select("tr.table_body")
    for row in rows:
        try:
            # 공지글 스킵
            if "notice" in row.get("class", []):
                continue

            # 제목
            title_a = row.select_one("td.subject a.subject_link")
            if not title_a:
                continue

            # strong 태그 안 텍스트 (BEST글), 없으면 그냥 텍스트
            strong = title_a.select_one("strong")
            title = strong.get_text(strip=True) if strong else title_a.get_text(strip=True)
            if not title:
                continue

            # 카테고리: td.divsn
            category_td = row.select_one("td.divsn")
            category = category_td.get_text(strip=True) if category_td else ""

            if not is_tech_deal(title, category):
                continue

            # URL / 게시글 ID
            href = title_a.get("href", "")
            post_id_match = re.search(r"/read/(\d+)", href)
            if not post_id_match:
                continue
            post_id = post_id_match.group(1)
            source_url = href if href.startswith("http") else BASE_URL + href

            # 추천수: td.recomd
            recomd_td = row.select_one("td.recomd")
            upvotes = 0
            if recomd_td:
                r_text = re.sub(r"[^\d]", "", recomd_td.get_text())
                upvotes = int(r_text) if r_text else 0

            # 댓글수: a.num_reply "(5)"
            reply_a = row.select_one("a.num_reply")
            comments_count = 0
            if reply_a:
                c_text = re.sub(r"[^\d]", "", reply_a.get_text())
                comments_count = int(c_text) if c_text else 0

            # 날짜: td.time
            time_td = row.select_one("td.time")
            posted_at = datetime.now()
            if time_td:
                posted_at = parse_posted_at(time_td.get_text(strip=True))

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
            print(f"[루리웹] 파싱 오류: {e}")
            continue

    print(f"[루리웹] 페이지 {page}: {len(deals)}개 전자제품 핫딜 수집")
    return deals


def crawl(pages: int = 3) -> list[RawDeal]:
    all_deals: list[RawDeal] = []
    for page in range(1, pages + 1):
        all_deals.extend(fetch_list_page(page=page, delay=3.0))
    return all_deals
