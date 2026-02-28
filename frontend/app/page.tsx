export default async function HomePage() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  let deals: any[] = [];
  try {
    const res = await fetch(`${API_URL}/api/v1/deals?size=40`, {
      next: { revalidate: 300 }, // 5분 캐시
    });
    if (res.ok) {
      const data = await res.json();
      deals = data.items ?? [];
    }
  } catch {
    // API 서버가 꺼져 있으면 빈 목록 표시
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "16px" }}>최신 핫딜</h1>

      {deals.length === 0 ? (
        <p style={{ color: "#888" }}>현재 표시할 딜이 없습니다. 잠시 후 다시 확인해주세요.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "16px",
          }}
        >
          {deals.map((deal: any) => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </div>
      )}
    </div>
  );
}

function DealCard({ deal }: { deal: any }) {
  const priceStr = deal.price != null
    ? `${deal.price.toLocaleString("ko-KR")}원`
    : "가격 미상";

  return (
    <div
      style={{
        background: "#fff",
        borderRadius: "8px",
        padding: "16px",
        boxShadow: "0 1px 4px rgba(0,0,0,.1)",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
      }}
    >
      {/* 소스 배지 */}
      <span
        style={{
          fontSize: "0.75rem",
          background: "#e8f0fe",
          color: "#3c4fe0",
          padding: "2px 8px",
          borderRadius: "12px",
          width: "fit-content",
        }}
      >
        {deal.source_name}
      </span>

      {/* 제목 (원문 링크) */}
      <a
        href={deal.source_url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ fontWeight: "bold", color: "#111", textDecoration: "none", lineHeight: 1.4 }}
      >
        {deal.title}
      </a>

      {/* 가격 */}
      <p style={{ color: "#e63946", fontWeight: "bold", margin: 0 }}>{priceStr}</p>

      {/* 구매 링크 */}
      {deal.mall_url && (
        <a
          href={deal.mall_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: "#1a1a2e",
            color: "#fff",
            padding: "6px 12px",
            borderRadius: "6px",
            textDecoration: "none",
            fontSize: "0.85rem",
            textAlign: "center",
          }}
        >
          쇼핑몰 바로가기
        </a>
      )}

      {/* 메타 정보 */}
      <p style={{ fontSize: "0.75rem", color: "#888", margin: 0 }}>
        추천 {deal.upvotes ?? 0} · 댓글 {deal.comments_count ?? 0}
      </p>
    </div>
  );
}
