"""
전자제품 모델명 추출기
제목에서 모델명 패턴을 정규식으로 추출
"""
import re
from typing import Optional

# 모델명 패턴 (우선순위 순)
MODEL_PATTERNS = [
    # GPU: RTX 4090, GTX 1080 Ti, RX 7900 XTX
    r"\b(RTX\s*\d{4}(?:\s*Ti)?(?:\s*Super)?|GTX\s*\d{4}(?:\s*Ti)?|RX\s*\d{4}(?:\s*XT|XTX|GRE)?)\b",
    # CPU: i5-13600K, Ryzen 5 7600X, Core Ultra 9
    r"\b((?:Core\s*)?(?:i[3579]|Ultra\s*[579])-\d{4,5}[A-Z]{0,3}|Ryzen\s*[357]\s*\d{4}[A-Z]{0,3})\b",
    # 맥북: MacBook Pro 14, MacBook Air M3
    r"\b(MacBook\s*(?:Pro|Air)\s*(?:\d{2})?(?:\s*M\d)?)\b",
    # 아이폰: iPhone 16 Pro Max, iPhone 15
    r"\b(iPhone\s*\d{1,2}(?:\s*(?:Pro|Plus|Max|Mini))*)\b",
    # 갤럭시: Galaxy S25 Ultra, Galaxy Tab S10
    r"\b(Galaxy\s*(?:S|Z|A|Tab)\d{1,2}(?:\+|Ultra|FE|Plus)?)\b",
    # 아이패드: iPad Pro 13, iPad Air M2
    r"\b(iPad\s*(?:Pro|Air|Mini)?\s*(?:\d{1,2})?(?:\s*M\d)?)\b",
    # 모니터 시리즈: LG 27GP850, DELL U2723D
    r"\b([A-Z]{2,5}\s*\d{2}[A-Z]{0,2}\d{3,4}[A-Z]{0,3})\b",
    # SSD/메모리: 970 EVO, WD Black SN850
    r"\b((?:970|980|990)\s*(?:EVO|PRO)|WD\s*(?:Black|Blue|Red)\s*\w{2,6}|Crucial\s*\w{2,6})\b",
    # 일반 모델번호: 대문자+숫자 5자 이상
    r"\b([A-Z][A-Z0-9\-]{4,})\b",
]

# 노이즈 패턴 (모델명이 아닌 것)
NOISE_PATTERNS = {
    "HTTPS", "HTTP", "HTML", "JSON", "API", "URL", "FREE",
    "SALE", "BEST", "DEAL", "OPEN", "SOLD", "OUT",
}


def extract_model(title: str) -> Optional[str]:
    """
    제목에서 전자기기 모델명 추출

    Args:
        title: 핫딜 게시글 제목

    Returns:
        추출된 모델명 (없으면 None)

    Examples:
        >>> extract_model("삼성 OLED G9 34인치 역대급 핫딜")
        'OLED G9'
        >>> extract_model("RTX 4090 FE 파격 할인")
        'RTX 4090'
        >>> extract_model("아이폰 16 Pro Max 역대 최저가")
        'iPhone 16 Pro Max'
    """
    title_upper = title.upper()

    for pattern in MODEL_PATTERNS:
        matches = re.findall(pattern, title, re.IGNORECASE)
        for match in matches:
            model = match.strip()
            # 노이즈 필터링
            if model.upper() in NOISE_PATTERNS:
                continue
            # 너무 짧으면 스킵
            if len(model) < 3:
                continue
            return model

    return None


def extract_category_hint(title: str) -> Optional[str]:
    """
    제목에서 카테고리 힌트 추출

    Returns:
        카테고리 이름 힌트 (DB 카테고리명과 매핑용)
    """
    title_lower = title.lower()

    category_map = {
        "그래픽카드": ["그래픽카드", "gpu", "rtx", "gtx", "rx "],
        "CPU/메인보드": ["cpu", "ryzen", "i5", "i7", "i9", "intel", "amd", "메인보드"],
        "메모리/SSD": ["ssd", "nvme", "ddr", "ram", "메모리", "nas"],
        "모니터": ["모니터", "monitor", "oled", "qled", "ips", "va "],
        "노트북": ["노트북", "laptop", "맥북", "macbook"],
        "스마트폰/태블릿": ["스마트폰", "아이폰", "갤럭시", "iphone", "galaxy", "아이패드", "ipad", "태블릿"],
        "주변기기": ["키보드", "마우스", "이어폰", "헤드폰", "스피커", "웹캠", "패드"],
    }

    for category, keywords in category_map.items():
        if any(kw in title_lower for kw in keywords):
            return category

    return "기타 전자제품"
