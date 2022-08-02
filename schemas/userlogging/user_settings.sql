-- Table: public.user_settings

-- DROP TABLE IF EXISTS public.user_settings;

CREATE TABLE IF NOT EXISTS public.user_settings
(
    user_id bigint NOT NULL,
    discriminator boolean,
    username boolean,
    avatar boolean,
    CONSTRAINT user_settings_pkey PRIMARY KEY (user_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_settings
    OWNER to "AV";