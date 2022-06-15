-- Table: public.afk
-- DROP TABLE IF EXISTS public.afk;

CREATE TABLE IF NOT EXISTS public.afk
(
    user_id bigint NOT NULL,
    reason text COLLATE pg_catalog."default",
    "time" timestamp with time zone,
    CONSTRAINT afk_pkey PRIMARY KEY (user_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.afk
    OWNER to "AV";

COMMENT ON TABLE public.afk
    IS 'stores afk metadata';