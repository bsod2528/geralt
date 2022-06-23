-- Table: public.ticket_init

-- DROP TABLE IF EXISTS public.ticket_init;

CREATE TABLE IF NOT EXISTS public.ticket_init
(
    id bigint NOT NULL DEFAULT nextval('ticket_init_id_seq'::regclass),
    guild_id bigint NOT NULL,
    category_id text COLLATE pg_catalog."default",
    sent_message_id bigint,
    sent_channel_id bigint,
    jump_url text COLLATE pg_catalog."default",
    panel_description text COLLATE pg_catalog."default",
    message_description text COLLATE pg_catalog."default",
    CONSTRAINT ticket_init_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.ticket_init
    OWNER to "AV";

COMMENT ON TABLE public.ticket_init
    IS 'meant for initialization of ticket system per guild';