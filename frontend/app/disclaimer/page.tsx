import { Metadata } from "next";

export const metadata: Metadata = {
  title: "이용 고지 및 면책 조항 | TechDeal-Hub",
};

export default function DisclaimerPage() {
  return (
    <div style={{ maxWidth: 760, margin: "0 auto", lineHeight: 1.8 }}>
      <h1>이용 고지 및 면책 조항</h1>

      <section>
        <h2>1. 서비스 성격</h2>
        <p>
          TechDeal-Hub는 비영리 목적으로 운영되는 정보 집약(aggregator) 서비스입니다.
          광고 수익, 제휴 수익, 유료 구독 등 어떠한 상업적 수익도 추구하지 않습니다.
        </p>
      </section>

      <section>
        <h2>2. 저작권 및 콘텐츠 귀속</h2>
        <p>
          본 서비스에 표시되는 게시물 제목, 이미지, 가격 정보 등의 저작권은
          <strong>원 게시물 작성자 및 해당 커뮤니티 운영자</strong>에게 있습니다.
          본 서비스는 아래 출처 사이트의 공개된 게시물을 요약 링크 형태로만 제공하며,
          원문 전체를 복제하거나 게재하지 않습니다.
        </p>
        <ul>
          <li>뽐뿌 (ppomppu.co.kr)</li>
          <li>클리앙 (clien.net)</li>
          <li>퀘이사존 (quasarzone.com)</li>
          <li>루리웹 (ruliweb.com)</li>
        </ul>
        <p>
          모든 딜 카드의 &quot;원문 보기&quot; 링크는 해당 출처 사이트의 원래 게시물로 직접 연결됩니다.
        </p>
      </section>

      <section>
        <h2>3. robots.txt 준수</h2>
        <p>
          본 서비스의 크롤러는 각 사이트의 robots.txt를 확인하고 준수합니다.
          크롤링이 명시적으로 금지된 사이트(예: 펨코)는 수집 대상에서 제외하였습니다.
          크롤러는 사이트 부하를 최소화하기 위해 요청 간격을 1초 이상 유지하고
          Bot임을 명시하는 User-Agent(TechDealBot/1.0)를 사용합니다.
        </p>
      </section>

      <section>
        <h2>4. 면책 사항</h2>
        <p>
          본 서비스는 가격 정확성, 딜의 유효성, 구매 결과에 대해 어떠한 보증도 하지 않습니다.
          구매 전 반드시 원 게시물 및 판매 사이트에서 최신 정보를 확인하시기 바랍니다.
        </p>
      </section>

      <section>
        <h2>5. 저작권 침해 신고</h2>
        <p>
          귀하의 콘텐츠가 본 서비스에 부적절하게 표시된다고 판단하시는 경우,
          아래 이메일로 연락 주시면 <strong>24시간 이내</strong>에 해당 콘텐츠를 삭제합니다.
        </p>
        <p>
          신고 이메일:{" "}
          <a href="mailto:contact@techdeal-hub.local">contact@techdeal-hub.local</a>
        </p>
        <p>신고 시 다음 정보를 포함해 주세요:</p>
        <ul>
          <li>권리자 성명 / 운영자명</li>
          <li>침해 주장 콘텐츠의 URL</li>
          <li>원본 콘텐츠의 URL 또는 증거 자료</li>
        </ul>
      </section>

      <section>
        <h2>6. 정책 변경</h2>
        <p>
          운영 방침은 관련 법령 변경 또는 출처 사이트의 정책 변경에 따라 갱신될 수 있습니다.
          중요한 변경 사항은 이 페이지에 게시합니다.
        </p>
        <p>최종 갱신일: 2026-02-28</p>
      </section>
    </div>
  );
}
