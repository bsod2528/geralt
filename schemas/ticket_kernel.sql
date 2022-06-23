-- Table: public.ticket_kernel

-- DROP TABLE IF EXISTS public.ticket_kernel;

CREATE TABLE IF NOT EXISTS public.ticket_kernel
(
    ticket_id bigint NOT NULL DEFAULT nextval('ticket_kernel_ticket_id_seq'::regclass),
    guild_id bigint NOT NULL,
    invoker_id bigint NOT NULL,
    invoked_at timestamp with time zone,
    CONSTRAINT ticket_kernel_pkey PRIMARY KEY (ticket_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.ticket_kernel
    OWNER to "AV";