-- ══════════════════════════════════════════════════════════════
-- SETUP SUPABASE — Sistema de Atendimentos Rio Verde v3
-- Execute em: Supabase → SQL Editor → New Query
-- ══════════════════════════════════════════════════════════════

-- ── 1. Contribuintes ─────────────────────────────────────────
-- UUID vem da API Gove (campo uuid do objeto recipient)
CREATE TABLE IF NOT EXISTS public.contribuintes (
    uuid        TEXT        PRIMARY KEY,   -- uuid retornado pela API Gove
    name        TEXT,
    email       TEXT,
    created_at  TIMESTAMPTZ,
    synced_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.contribuintes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "contribuintes_select" ON public.contribuintes;
DROP POLICY IF EXISTS "contribuintes_insert" ON public.contribuintes;
DROP POLICY IF EXISTS "contribuintes_update" ON public.contribuintes;
CREATE POLICY "contribuintes_select" ON public.contribuintes FOR SELECT USING (TRUE);
CREATE POLICY "contribuintes_insert" ON public.contribuintes FOR INSERT WITH CHECK (TRUE);
CREATE POLICY "contribuintes_update" ON public.contribuintes FOR UPDATE USING (TRUE);

-- ── 2. Atendentes ─────────────────────────────────────────────
-- UUID vem da API Gove (campo uuid do objeto agent)
CREATE TABLE IF NOT EXISTS public.atendentes (
    uuid        TEXT        PRIMARY KEY,
    name        TEXT,
    email       TEXT,
    created_at  TIMESTAMPTZ,
    synced_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.atendentes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "atendentes_select" ON public.atendentes;
DROP POLICY IF EXISTS "atendentes_insert" ON public.atendentes;
DROP POLICY IF EXISTS "atendentes_update" ON public.atendentes;
CREATE POLICY "atendentes_select" ON public.atendentes FOR SELECT USING (TRUE);
CREATE POLICY "atendentes_insert" ON public.atendentes FOR INSERT WITH CHECK (TRUE);
CREATE POLICY "atendentes_update" ON public.atendentes FOR UPDATE USING (TRUE);

-- ── 3. Setores ────────────────────────────────────────────────
-- UUID vem da API Gove (campo uuid do objeto sector)
CREATE TABLE IF NOT EXISTS public.setores (
    uuid        TEXT        PRIMARY KEY,
    name        TEXT,
    acronym     TEXT,
    synced_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.setores ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "setores_select" ON public.setores;
DROP POLICY IF EXISTS "setores_insert" ON public.setores;
DROP POLICY IF EXISTS "setores_update" ON public.setores;
CREATE POLICY "setores_select" ON public.setores FOR SELECT USING (TRUE);
CREATE POLICY "setores_insert" ON public.setores FOR INSERT WITH CHECK (TRUE);
CREATE POLICY "setores_update" ON public.setores FOR UPDATE USING (TRUE);

-- ── 4. Atendimentos ───────────────────────────────────────────
-- Chave primária = id do chat na API Gove
-- FKs para contribuinte, atendente e setor via uuid
CREATE TABLE IF NOT EXISTS public.atendimentos (
    id                  TEXT        PRIMARY KEY,   -- id do chat (API Gove)
    protocolo           TEXT,
    status              TEXT,
    tipo                TEXT,
    contribuinte_uuid   TEXT REFERENCES public.contribuintes(uuid) ON DELETE SET NULL,
    atendente_uuid      TEXT REFERENCES public.atendentes(uuid)    ON DELETE SET NULL,
    setor_uuid          TEXT REFERENCES public.setores(uuid)        ON DELETE SET NULL,
    -- Campos adicionais da API (armazena tudo)
    dados_extras        JSONB,                     -- demais campos do JSON da API
    aberto_em           TIMESTAMPTZ,
    encerrado_em        TIMESTAMPTZ,
    synced_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_atend_status      ON public.atendimentos(status);
CREATE INDEX IF NOT EXISTS idx_atend_aberto_em   ON public.atendimentos(aberto_em DESC);
CREATE INDEX IF NOT EXISTS idx_atend_contribuinte ON public.atendimentos(contribuinte_uuid);
CREATE INDEX IF NOT EXISTS idx_atend_atendente    ON public.atendimentos(atendente_uuid);
CREATE INDEX IF NOT EXISTS idx_atend_setor        ON public.atendimentos(setor_uuid);

ALTER TABLE public.atendimentos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "atendimentos_select" ON public.atendimentos;
DROP POLICY IF EXISTS "atendimentos_insert" ON public.atendimentos;
DROP POLICY IF EXISTS "atendimentos_update" ON public.atendimentos;
CREATE POLICY "atendimentos_select" ON public.atendimentos FOR SELECT USING (TRUE);
CREATE POLICY "atendimentos_insert" ON public.atendimentos FOR INSERT WITH CHECK (TRUE);
CREATE POLICY "atendimentos_update" ON public.atendimentos FOR UPDATE USING (TRUE);

-- ── 5. View: atendimentos completa (join com nomes) ───────────
CREATE OR REPLACE VIEW public.v_atendimentos AS
SELECT
    a.id,
    a.protocolo,
    a.status,
    a.tipo,
    c.name                              AS contribuinte_nome,
    c.email                             AS contribuinte_email,
    ag.name                             AS atendente_nome,
    ag.email                            AS atendente_email,
    s.name                              AS setor_nome,
    s.acronym                           AS setor_sigla,
    a.aberto_em,
    a.encerrado_em,
    a.synced_at,
    a.updated_at
FROM public.atendimentos a
LEFT JOIN public.contribuintes c  ON c.uuid  = a.contribuinte_uuid
LEFT JOIN public.atendentes    ag ON ag.uuid = a.atendente_uuid
LEFT JOIN public.setores       s  ON s.uuid  = a.setor_uuid;

-- ── 6. Verificação final ──────────────────────────────────────
SELECT
    'contribuintes'  AS tabela, COUNT(*) AS registros FROM public.contribuintes
UNION ALL SELECT 'atendentes',  COUNT(*) FROM public.atendentes
UNION ALL SELECT 'setores',     COUNT(*) FROM public.setores
UNION ALL SELECT 'atendimentos',COUNT(*) FROM public.atendimentos;
