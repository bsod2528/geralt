-- Table: public.verification

-- DROP TABLE IF EXISTS public.verification;

CREATE TABLE IF NOT EXISTS public.verification
(
    guild_id bigint NOT NULL,
    question text COLLATE pg_catalog."default",
    answer text COLLATE pg_catalog."default",
    role_id text COLLATE pg_catalog."default",
    channel_id text COLLATE pg_catalog."default",
    message_id text COLLATE pg_catalog."default",
    CONSTRAINT verification_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.verification
    OWNER to "AV";