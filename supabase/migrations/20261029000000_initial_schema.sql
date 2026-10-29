-- =============================================================================
-- KisanSathi Rajasthan: Initial Schema & Row Level Security (RLS) Policies
-- Migration: 20261029000000_initial_schema.sql
-- Database: Supabase Postgres with pgvector
-- =============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- -----------------------------------------------------------------------------
-- Table 1: profiles
-- Stores user preferences linked to Supabase Auth
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    language TEXT NOT NULL DEFAULT 'hi' CHECK (language IN ('hi', 'en')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- Table 2: farms
-- Farm profile personalizing yield, price, weather, and advisor recommendations
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.farms (
    farm_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    district TEXT NOT NULL,
    tehsil TEXT NOT NULL,
    crop TEXT NOT NULL,
    land_hectare NUMERIC(10, 2) NOT NULL CHECK (land_hectare > 0),
    irrigation TEXT NOT NULL CHECK (irrigation IN ('canal', 'tubewell', 'well', 'rainfed')),
    sowing_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_farms_user_id ON public.farms(user_id);
CREATE INDEX IF NOT EXISTS idx_farms_district_crop ON public.farms(district, crop);

ALTER TABLE public.farms ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own farms"
    ON public.farms FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own farms"
    ON public.farms FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own farms"
    ON public.farms FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own farms"
    ON public.farms FOR DELETE
    USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- Table 3: messages
-- Advisor chat history with citations and model versions
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    intent TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at DESC);

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own messages"
    ON public.messages FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own messages"
    ON public.messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- Table 4: disease_predictions
-- Crop disease predictions from browser ONNX or server fallback
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disease_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    crop TEXT NOT NULL,
    predicted_label TEXT NOT NULL,
    confidence NUMERIC(5, 4) NOT NULL,
    model_version TEXT NOT NULL,
    image_path TEXT, -- Nullable: stored ONLY if user opted in
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_disease_user_id ON public.disease_predictions(user_id);

ALTER TABLE public.disease_predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own disease predictions"
    ON public.disease_predictions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own disease predictions"
    ON public.disease_predictions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- Table 5: mandi_prices
-- Historical & current APMC mandi commodity prices in Rajasthan
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.mandi_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mandi TEXT NOT NULL,
    commodity TEXT NOT NULL,
    price_date DATE NOT NULL,
    min_price NUMERIC(10, 2) NOT NULL,
    max_price NUMERIC(10, 2) NOT NULL,
    modal_price NUMERIC(10, 2) NOT NULL,
    arrivals NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT mandi_commodity_date_unique UNIQUE (mandi, commodity, price_date)
);

CREATE INDEX IF NOT EXISTS idx_mandi_prices_lookup ON public.mandi_prices(mandi, commodity, price_date DESC);

ALTER TABLE public.mandi_prices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read-only access to mandi prices"
    ON public.mandi_prices FOR SELECT
    TO authenticated, anon
    USING (true);

-- -----------------------------------------------------------------------------
-- Table 6: yield_history
-- Historical district agricultural production records for Rajasthan
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.yield_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL,
    crop TEXT NOT NULL,
    season TEXT NOT NULL,
    year INTEGER NOT NULL,
    area_ha NUMERIC(12, 2),
    production NUMERIC(12, 2),
    yield_kg_ha NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT district_crop_season_year_unique UNIQUE (district, crop, season, year)
);

CREATE INDEX IF NOT EXISTS idx_yield_history_lookup ON public.yield_history(district, crop, season, year DESC);

ALTER TABLE public.yield_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read-only access to yield history"
    ON public.yield_history FOR SELECT
    TO authenticated, anon
    USING (true);

-- -----------------------------------------------------------------------------
-- Table 7: kb_chunks
-- Chunked Rajasthan agricultural manuals with Gemini 768-dim vector embeddings
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    doc_title TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(768),
    language TEXT NOT NULL DEFAULT 'hi',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Cosine distance index for fast RAG retrieval
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding 
    ON public.kb_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

ALTER TABLE public.kb_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read-only access to knowledge base chunks"
    ON public.kb_chunks FOR SELECT
    TO authenticated, anon
    USING (true);

-- Helper RPC for pgvector similarity search
CREATE OR REPLACE FUNCTION match_kb_chunks (
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.60,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    source TEXT,
    doc_title TEXT,
    chunk_text TEXT,
    language TEXT,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        kb_chunks.id,
        kb_chunks.source,
        kb_chunks.doc_title,
        kb_chunks.chunk_text,
        kb_chunks.language,
        1 - (kb_chunks.embedding <=> query_embedding) AS similarity
    FROM public.kb_chunks
    WHERE 1 - (kb_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- -----------------------------------------------------------------------------
-- Table 8: feedback
-- Farmer feedback and ground-truth validation outcomes
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES public.messages(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating IN (-1, 1, 2, 3, 4, 5)),
    actual_outcome TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback(user_id);

ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own feedback"
    ON public.feedback FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert feedback"
    ON public.feedback FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- Table 9: training_images
-- Catalog of images with sha256 hash for reproducible ML model training
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.training_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_hash TEXT UNIQUE NOT NULL,
    crop TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL,
    split TEXT NOT NULL CHECK (split IN ('train', 'val', 'test')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_training_images_split ON public.training_images(crop, label, split);

ALTER TABLE public.training_images ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read training image catalog"
    ON public.training_images FOR SELECT
    TO authenticated
    USING (true);
