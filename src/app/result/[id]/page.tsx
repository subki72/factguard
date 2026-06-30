"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getAnalysis } from "@/lib/api-client";
import type { AnalysisDetail } from "@/lib/api-client";
import ScoreDisplay from "@/components/ScoreDisplay";
import { Search, ThumbsUp, ThumbsDown } from "lucide-react";

export default function ResultPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const res = await getAnalysis(id);
      if (res.success && res.data) {
        setData(res.data);
      } else {
        setError(res.error || "Analisis tidak ditemukan.");
      }
      setLoading(false);
    }
    if (id) load();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="skeleton h-48 rounded-2xl mb-6" />
        <div className="skeleton h-32 rounded-2xl mb-4" />
        <div className="skeleton h-24 rounded-2xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <Search className="w-16 h-16 mx-auto mb-4 text-gray-500" />
        <h1 className="text-xl font-bold mb-3">Analisis Tidak Ditemukan</h1>
        <p style={{ color: "var(--foreground-muted)" }}>{error}</p>
        <a href="/" className="btn-primary inline-block mt-6">
          Kembali ke Beranda
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-2xl font-bold mb-6">
        Hasil <span className="gradient-text">Analisis</span>
      </h1>

      {/* Score display */}
      <ScoreDisplay result={data} />

      {/* Extracted text preview */}
      <div className="glass-card p-6 mt-6 animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
        <h2 className="text-sm font-semibold mb-3">Teks yang Dianalisis</h2>
        <p
          className="text-sm leading-relaxed whitespace-pre-wrap"
          style={{ color: "var(--foreground-muted)", maxHeight: "200px", overflow: "auto" }}
        >
          {data.extracted_text}
        </p>
      </div>

      {/* Community section */}
      <div className="glass-card p-6 mt-6 animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
        <h2 className="text-sm font-semibold mb-4">Diskusi Komunitas</h2>

        {/* Votes */}
        <div className="flex items-center gap-4 mb-6">
          <button
            className="btn-ghost flex items-center gap-2 text-sm"
            style={{ borderColor: "rgba(16, 185, 129, 0.3)" }}
          >
            <ThumbsUp className="w-4 h-4" /> Setuju ({data.vote_agree})
          </button>
          <button
            className="btn-ghost flex items-center gap-2 text-sm"
            style={{ borderColor: "rgba(239, 68, 68, 0.3)" }}
          >
            <ThumbsDown className="w-4 h-4" /> Tidak Setuju ({data.vote_disagree})
          </button>
        </div>

        {/* Comments */}
        {data.comments && data.comments.length > 0 ? (
          <div className="space-y-3">
            {data.comments.map((comment) => (
              <div
                key={comment.id}
                className="p-4 rounded-xl"
                style={{ background: "var(--background-secondary)" }}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">{comment.user_name}</span>
                  <span className="text-xs" style={{ color: "var(--foreground-muted)" }}>
                    {new Date(comment.created_at).toLocaleDateString("id-ID")}
                  </span>
                </div>
                <p className="text-sm" style={{ color: "var(--foreground-muted)" }}>
                  {comment.content}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm" style={{ color: "var(--foreground-muted)", opacity: 0.6 }}>
            Belum ada komentar. Login untuk menjadi yang pertama berkomentar.
          </p>
        )}
      </div>

      {/* Meta info */}
      <div className="text-center mt-6">
        <p className="text-xs" style={{ color: "var(--foreground-muted)", opacity: 0.5 }}>
          ID: {data.analysis_id} • Dianalisis pada{" "}
          {new Date(data.created_at).toLocaleString("id-ID")}
        </p>
      </div>
    </div>
  );
}
