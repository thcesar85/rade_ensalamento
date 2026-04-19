-- Migration: Adicionar coluna 'active' em tbGroup se não existir
-- Data: 2025-04-18

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name='tbGroup' AND column_name='active'
    ) THEN
        ALTER TABLE public."tbGroup"
        ADD COLUMN active BOOLEAN DEFAULT false;
        
        RAISE NOTICE 'Coluna active adicionada em tbGroup';
    ELSE
        RAISE NOTICE 'Coluna active já existe em tbGroup';
    END IF;
END
$$;
