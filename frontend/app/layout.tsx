import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "TechDeal-Hub | 전자제품 핫딜 모음",
  description: "뽐뿌, 클리앙, 퀘이사존, 루리웹 핫딜을 한 곳에서",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body style={{ margin: 0, fontFamily: "sans-serif", background: "#f5f5f5" }}>
        <header style={{ background: "#1a1a2e", color: "#fff", padding: "12px 24px" }}>
          <Link href="/" style={{ color: "#fff", textDecoration: "none", fontWeight: "bold", fontSize: "1.2rem" }}>
            TechDeal-Hub
          </Link>
        </header>

        <main style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 16px" }}>
          {children}
        </main>

        <footer style={{ background: "#222", color: "#aaa", padding: "24px 16px", marginTop: "40px", fontSize: "0.85rem" }}>
          <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            <p>
              TechDeal-Hub는 비영리 정보 집약 서비스입니다.
              게시물 원문은 각 출처 사이트에 귀속되며, 본 서비스는 링크와 요약 정보만을 제공합니다.
            </p>
            <p>
              각 게시물의 저작권은 원저작자에게 있습니다. 저작권 관련 문의는{" "}
              <a href="mailto:contact@techdeal-hub.local" style={{ color: "#ccc" }}>
                contact@techdeal-hub.local
              </a>
              로 보내주시면 즉시 조치합니다.
            </p>
            <p>
              <Link href="/disclaimer" style={{ color: "#ccc" }}>이용 고지 및 면책 조항</Link>
              {" | "}
              수집 출처: 뽐뿌, 클리앙, 퀘이사존, 루리웹
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
