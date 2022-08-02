-- Table: public.username_history

-- DROP TABLE IF EXISTS public.username_history;

CREATE TABLE IF NOT EXISTS public.username_history
(
    user_id bigint,
    username text COLLATE pg_catalog."default",
    "timestamp" timestamp with time zone
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.username_history
    OWNER to "AV";