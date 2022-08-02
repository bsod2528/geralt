-- Table: public.avatar_history

-- DROP TABLE IF EXISTS public.avatar_history;

CREATE TABLE IF NOT EXISTS public.avatar_history
(
    user_id bigint,
    avatar bytea,
    "timestamp" timestamp with time zone,
    format text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.avatar_history
    OWNER to "AV";