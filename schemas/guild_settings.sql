-- Table: public.guild_settings

-- DROP TABLE IF EXISTS public.guild_settings;

CREATE TABLE IF NOT EXISTS public.guild_settings
(
    guild_id bigint NOT NULL,
    convert_url_to_webhook text COLLATE pg_catalog."default",
    CONSTRAINT guild_settings_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.guild_settings
    OWNER to "AV";

COMMENT ON TABLE public.guild_settings
    IS 'for now, it just holds whether to convert emoji url to webhook :handshake:';