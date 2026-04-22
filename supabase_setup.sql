-- ══════════════════════════════════════════════════════════════
-- SETUP SUPABASE — Sistema de Atendimentos Rio Verde (v2)
-- Execute em: Supabase → SQL Editor → New Query
-- ══════════════════════════════════════════════════════════════

-- ── 1. Tabela profiles ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id         UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email      TEXT        NOT NULL,
    nome       TEXT        NOT NULL,
    perfil     TEXT        NOT NULL DEFAULT 'usuario'
                           CHECK (perfil IN ('admin', 'usuario')),
    aprovado   BOOLEAN     NOT NULL DEFAULT FALSE,
    ativo      BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2. RLS — qualquer autenticado lê/atualiza o próprio ───────
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Leitura: autenticado lê qualquer perfil (necessário para verificar aprovação)
CREATE POLICY "autenticado_le_profiles"
    ON public.profiles FOR SELECT
    USING (auth.role() = 'authenticated');

-- Atualização: admin pode atualizar qualquer perfil
CREATE POLICY "admin_atualiza_profiles"
    ON public.profiles FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND perfil = 'admin'
        )
    );

-- Inserção: o próprio trigger insere (via service role)
CREATE POLICY "service_insere_profiles"
    ON public.profiles FOR INSERT
    WITH CHECK (TRUE);

-- ── 3. Trigger: cria perfil ao registrar usuário ──────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, nome, aprovado)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'nome',
            SPLIT_PART(NEW.email, '@', 1)
        ),
        FALSE   -- toda conta nova fica pendente
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ── 4. Promover admin ─────────────────────────────────────────
-- Execute DEPOIS de criar sua conta no sistema:
UPDATE public.profiles
SET perfil = 'admin', aprovado = TRUE
WHERE email = 'arlindo.mendonca@outlook.com';

-- ── 5. Verificar ─────────────────────────────────────────────
SELECT id, email, nome, perfil, aprovado, ativo, created_at
FROM public.profiles
ORDER BY created_at DESC;
