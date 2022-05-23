-- Table: public.guild_info
-- DROP TABLE IF EXISTS public.guild_info;

CREATE TABLE IF NOT EXISTS public.guild_info
(
    id bigint NOT NULL,
    guild_name text COLLATE pg_catalog."default" NOT NULL,
    owner_id bigint NOT NULL,
    owner_name text COLLATE pg_catalog."default",
    CONSTRAINT guild_info_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.guild_info
    OWNER to "AV";

COMMENT ON TABLE public.guild_info
    IS 'logs new guilds information upon joining';