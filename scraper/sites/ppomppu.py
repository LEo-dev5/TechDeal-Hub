"""
뽐뿌 핫딜 게시판 크롤러
대상: https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu
"""
import random
import time
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.ppomppu.co.kr"
LIST_URL = f"{BASE_URL}/zboard/zboard.php?id=ppomppu"

HEADERS = {
    "User-Agent": "TechDealBot/1.0 (+https://github.com/LEo-dev5/TechDeal-Hub)",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SOLD_OUT_KEYWORDS = ["[종료]", "[품절]", "품절", "마감", "sold out", "soldout"]

# 전자제품 키워드 (카테고리 필터링)
TECH_KEYWORDS = [
    "노트북", "맥북", "맥북프로", "맥북에어",
    "모니터", "그래픽카드", "gpu", "rtx", "gtx", "rx ",
    "cpu", "ryzen", "intel", "i5", "i7", "i9",
    "ssd", "nvme", "ddr", "ram", "메모리",
    "스마트폰", "아이폰", "갤럭시", "아이패드",
    "이어폰", "헤드폰", "스피커", "키보드", "마우스",
    "nas", "공유기", "카메라", "렌즈", "프린터",
    "tv", "oled", "qled", "청소기", "에어팟",
    "충전기", "충전", "케이블", "허브", "블루투스",
    "apple", "samsung", "lg전자", "삼성", "애플",
    "케이스", "배터리", "보조배터리", "usb",
    "게이밍", "gaming", "조이스틱", "패드",
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


def parse_price(text: str) -> Optional[int]:
    """가격 텍스트에서 숫자 추출 (예: '299,000원' → 299000)"""
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else None


def parse_posted_at(text: str) -> Optional[datetime]:
    """날짜 텍스트 파싱 (예: '25/02/21 14:30' → datetime)"""
    text = text.strip()
    for fmt in ("%y/%m/%d %H:%M", "%Y/%m/%d %H:%M", "%y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def is_tech_deal(title: str) -> bool:
    """제목이 전자제품 관련인지 판별"""
    title_lower = title.lower()
    return any(kw in title_lower for kw in TECH_KEYWORDS)


def is_sold_out(title: str) -> bool:
    """품절/종료 여부 판별"""
    title_lower = title.lower()
    return any(kw in title_lower for kw in SOLD_OUT_KEYWORDS)


def fetch_list_page(page: int = 1, delay: float = 3.0) -> list[RawDeal]:
    """
    뽐뿌 핫딜 목록 페이지 크롤링

    Args:
        page: 페이지 번호 (1부터 시작)
        delay: 요청 전 대기 시간(초)

    Returns:
        RawDeal 리스트
    """
    if delay > 0:
        time.sleep(delay + random.uniform(0, 2))

    url = f"{LIST_URL}&page={page}"

    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"[뽐뿌] HTTP 오류: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    deals: list[RawDeal] = []

    # 뽐뿌 게시판 tr 목록 파싱 (실제 HTML: tr.baseList)
    rows = soup.select("tr.baseList")
    for row in rows:
        try:
            # 제목 링크: td.title > div.baseList-box > div.baseList-cover > a.baseList-title
            title_a = row.select_one("a.baseList-title")
            if not title_a:
                continue

            # span 내부 텍스트 (em 태그 제외하고 순수 제목만)
            em = title_a.select_one("em.baseList-head")
            if em:
                em.decompose()
            title = title_a.get_text(strip=True)
            if not title:
                continue

            # 전자제품 필터링
            if not is_tech_deal(title):
                continue

            # 게시글 ID와 URL
            href = title_a.get("href", "")
            post_id_match = re.search(r"no=(\d+)", href)
            if not post_id_match:
                continue
            post_id = post_id_match.group(1)
            source_url = BASE_URL + "/zboard/" + href if not href.startswith("http") else href

            # 쇼핑몰 링크 (없음 — 뽐뿌는 게시글 내부에 링크 있음)
            mall_url = None

            # 가격 (뽐뿌 목록에는 별도 가격 열 없음)
            price = None

            # 추천수: td.baseList-rec "3 - 0" 형식에서 첫 번째 숫자
            upvote_td = row.select_one("td.baseList-rec")
            upvotes = 0
            if upvote_td:
                upvote_nums = re.findall(r"\d+", upvote_td.get_text())
                upvotes = int(upvote_nums[0]) if upvote_nums else 0

            # 댓글수: span.baseList-c
            comment_span = row.select_one("span.baseList-c")
            comments_count = 0
            if comment_span:
                c_text = re.sub(r"[^\d]", "", comment_span.get_text())
                comments_count = int(c_text) if c_text else 0

            # 날짜: time.baseList-time (title 속성에 전체 날짜)
            time_el = row.select_one("time.baseList-time")
            posted_at = datetime.now()
            if time_el:
                # title 속성: "26.02.27 19:58:48", 텍스트: "26/02/27"
                dt_text = time_el.get("title") or time_el.get_text(strip=True)
                # title 속성 포맷: "26.02.27 19:58:48"
                for fmt in ("%y.%m.%d %H:%M:%S", "%y/%m/%d", "%y.%m.%d"):
                    try:
                        posted_at = datetime.strptime(dt_text.strip(), fmt)
                        break
                    except ValueError:
                        continue

            # 썸네일: a.baseList-thumb > img
            thumb_img = row.select_one("a.baseList-thumb img")
            thumbnail_url = None
            if thumb_img:
                src = thumb_img.get("src", "")
                if src and "noimage" not in src:
                    thumbnail_url = "https:" + src if src.startswith("//") else src

            deals.append(RawDeal(
                source_post_id=post_id,
                title=title,
                source_url=source_url,
                mall_url=mall_url,
                price=price,
                upvotes=upvotes,
                comments_count=comments_count,
                posted_at=posted_at,
                thumbnail_url=thumbnail_url,
                is_active=not is_sold_out(title),
            ))

        except Exception as e:
            print(f"[뽐뿌] 파싱 오류: {e}")
            continue

    print(f"[뽐뿌] 페이지 {page}: {len(deals)}개 전자제품 핫딜 수집")
    return deals


def crawl(pages: int = 3) -> list[RawDeal]:
    """
    여러 페이지 크롤링

    Args:
        pages: 크롤링할 페이지 수

    Returns:
        전체 RawDeal 리스트
    """
    all_deals: list[RawDeal] = []
    for page in range(1, pages + 1):
        page_deals = fetch_list_page(page=page, delay=3.0)
        all_deals.extend(page_deals)
    return all_deals
