-- Table: public.prefix

-- DROP TABLE IF EXISTS public.prefix;

CREATE TABLE IF NOT EXISTS public.prefix
(
    guild_id bigint NOT NULL,
    guild_prefix text[] COLLATE pg_catalog."default" DEFAULT ARRAY[]::text[],
    CONSTRAINT prefix_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.prefix
    OWNER to "AV";