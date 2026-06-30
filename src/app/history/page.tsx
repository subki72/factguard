"use client";

import { useState, useEffect } from "react";
import type { AnalysisResult } from "@/lib/api-client";
import { getHistory } from "@/lib/api-client";
import { supabase } from "@/lib/supabase";

function getLabelBadgeClass(label: string): string {
  switch (label) {
    case "OBJEKTIF": return "badge-objektif";
    case "CENDERUNG_BIAS": return "badge-bias";
    case "SANGAT_MANIPULATIF": return "badge-manipulatif";
    default: return "";
  }
}

function getLabelDisplay(label: string): string {
  switch (label) {
    case "OBJEKTIF": return "Objektif";
    case "CENDERUNG_BIAS": return "Cenderung Bias";
    case "SANGAT_MANIPULATIF": return "Sangat Manipulatif";
    default: return label;
  }
}

function getScoreColor(score: number): string {
  if (score >= 70) return "var(--score-objektif)";
  if (score >= 40) return "var(--score-bias)";
  return "var(--score-manipulatif)";
}

const SESSION_KEY = "factguard_history";

interface HistoryItem extends AnalysisResult {
  timestamp: string;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistoryData() {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        // User is logged in, fetch from backend
        const backendHistory = await getHistory();
        if (backendHistory) {
          // Format timestamp if needed, but it already has 'timestamp'
          setHistory(backendHistory as HistoryItem[]);
        }
      } else {
        // Guest user, load from sessionStorage
        try {
          const stored = sessionStorage.getItem(SESSION_KEY);
          if (stored) {
            setHistory(JSON.parse(stored));
          }
        } catch {
          // sessionStorage not available
        }
      }
      setLoading(false);
    }
    
    fetchHistoryData();
  }, []);

  if (loading) {
    return <div className="p-16 text-center font-bold">Loading...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <div className="text-5xl mb-4">📋</div>
        <h1 className="text-2xl font-bold mb-3">Belum Ada Riwayat</h1>
        <p style={{ color: "var(--foreground-muted)" }}>
          Riwayat analisis Anda akan muncul di sini. Mulai analisis narasi politik
          untuk melihat hasilnya!
        </p>
        <p className="text-xs mt-4" style={{ color: "var(--foreground-muted)", opacity: 0.6 }}>
          💡 Login untuk menyimpan riwayat secara permanen. Sebagai guest, riwayat hanya tersimpan selama sesi browser aktif.
        </p>
        <a href="/" className="btn-primary inline-block mt-6">
          Mulai Analisis
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-2xl sm:text-3xl font-bold mb-2">
        Riwayat <span className="gradient-text">Analisis</span>
      </h1>
      <p className="text-sm mb-8" style={{ color: "var(--foreground-muted)" }}>
        {history.length} analisis tercatat dalam sesi ini
      </p>

      <div className="space-y-3">
        {history.map((item, i) => (
          <a
            key={i}
            href={`/result/${item.analysis_id}`}
            className="glass-card p-4 flex items-center justify-between gap-4 block transition-all hover:scale-[1.01]"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {item.extracted_text.slice(0, 80)}...
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--foreground-muted)" }}>
                {item.input_type} • {item.detected_language === "id" ? "🇮🇩" : "🇬🇧"}{" "}
                • {item.timestamp}
              </p>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-xl font-bold" style={{ color: getScoreColor(item.score) }}>
                {item.score}
              </span>
              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getLabelBadgeClass(item.label)}`}>
                {getLabelDisplay(item.label)}
              </span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
