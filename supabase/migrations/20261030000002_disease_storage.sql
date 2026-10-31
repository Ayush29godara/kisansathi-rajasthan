-- =============================================================================
-- Migration: 20261030000002_disease_storage.sql
-- Private Storage Bucket for Opt-in Crop Disease Diagnosis Photos
-- Security: Private bucket, signed URLs only, strict user ownership RLS
-- =============================================================================

-- 1. Create Private Storage Bucket for Opt-in Disease Photos
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'disease-photos',
    'disease-photos',
    false, -- STRICTLY PRIVATE: Access via authenticated signed URLs only
    5242880, -- 5 MB maximum file size
    ARRAY['image/jpeg', 'image/png']
)
ON CONFLICT (id) DO NOTHING;

-- 2. Storage RLS Policies: Scoped strictly to the authenticated farmer
CREATE POLICY "Users can upload their own disease photos"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'disease-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can view their own disease photos via signed URLs"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'disease-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can delete their own uploaded photos"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'disease-photos' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );
