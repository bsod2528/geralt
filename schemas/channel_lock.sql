-- Table: public.channel_lock

-- DROP TABLE IF EXISTS public.channel_lock;

CREATE TABLE IF NOT EXISTS public.channel_lock
(
    object_id bigint NOT NULL,
    channel_id bigint,
    guild_id bigint,
    object_type text COLLATE pg_catalog."default",
    queried_at timestamp with time zone,
    CONSTRAINT lock_pkey PRIMARY KEY (object_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.channel_lock
    OWNER to "AV";

COMMENT ON TABLE public.channel_lock
    IS 'stores role/member ids for viewing which channels got locked for which objects.';