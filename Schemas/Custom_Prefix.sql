-- Table: public.custom_prefix
-- DROP TABLE IF EXISTS public.custom_prefix;

CREATE TABLE IF NOT EXISTS public.custom_prefix
(
    guild_prefix text COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    guild_name text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT custom_prefix_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.custom_prefix
    OWNER to "AV";

COMMENT ON TABLE public.custom_prefix
    IS 'custom prefix for each guild';