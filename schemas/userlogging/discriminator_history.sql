-- Table: public.discriminator_history

-- DROP TABLE IF EXISTS public.discriminator_history;

CREATE TABLE IF NOT EXISTS public.discriminator_history
(
    user_id bigint,
    discriminator text COLLATE pg_catalog."default",
    "timestamp" timestamp with time zone
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.discriminator_history
    OWNER to "AV";