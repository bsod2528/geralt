-- Table: public.meta
-- DROP TABLE IF EXISTS public.meta;

CREATE TABLE IF NOT EXISTS public.meta
(
    command_name text COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    invoked_at timestamp with time zone,
    uses bigint DEFAULT 0,
    CONSTRAINT meta_pkey1 PRIMARY KEY (command_name, guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.meta
    OWNER to "AV";

COMMENT ON TABLE public.meta
    IS 'stores command usage count';