-- ============================================
-- AI Fake News Detection — Supabase Schema
-- Jalankan SQL ini di Supabase SQL Editor
-- ============================================

-- 1. Enable UUID extension (biasanya sudah enabled di Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Tabel Users (diisi otomatis saat login via Google OAuth)
-- Catatan: Supabase Auth sudah punya tabel auth.users bawaan.
-- Tabel ini adalah tabel profil tambahan di schema public.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id UUID UNIQUE NOT NULL,  -- referensi ke auth.users.id dari Supabase Auth
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabel Analyses (hasil analisis objektivitas)
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL jika guest
    input_type TEXT NOT NULL CHECK (input_type IN ('TEXT', 'URL', 'IMAGE')),
    raw_input TEXT NOT NULL,
    extracted_text TEXT NOT NULL,
    detected_language TEXT DEFAULT 'id',  -- 'id' atau 'en'
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    label TEXT NOT NULL CHECK (label IN ('OBJEKTIF', 'CENDERUNG_BIAS', 'SANGAT_MANIPULATIF')),
    reasoning TEXT NOT NULL,
    buzzer_indicators JSONB DEFAULT '[]'::jsonb,
    ip_hash TEXT,  -- Hash dari IP address (untuk rate limiting & privasi)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_label ON analyses(label);

-- 4. Tabel Crawled Articles (artikel dari portal berita yang dicrawl otomatis)
CREATE TABLE IF NOT EXISTS crawled_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_portal TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content_text TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    label TEXT NOT NULL CHECK (label IN ('OBJEKTIF', 'CENDERUNG_BIAS', 'SANGAT_MANIPULATIF')),
    reasoning TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crawled_articles_created_at ON crawled_articles(created_at DESC);
CREATE INDEX idx_crawled_articles_source ON crawled_articles(source_portal);

-- 5. Tabel Votes (upvote/downvote komunitas)
CREATE TABLE IF NOT EXISTS votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_agree BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(analysis_id, user_id)  -- 1 user hanya boleh vote 1x per analisis
);

CREATE INDEX idx_votes_analysis_id ON votes(analysis_id);

-- 6. Tabel Comments (komentar komunitas)
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comments_analysis_id ON comments(analysis_id);

-- 7. Tabel Audit Logs (pencatatan aktivitas sistem untuk keamanan)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- Bisa NULL untuk aksi anonim/guest
    ip_hash TEXT,
    action_type TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_action ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
