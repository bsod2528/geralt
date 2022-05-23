-- Table: public.snipe
-- DROP TABLE IF EXISTS public.snipe;

CREATE TABLE IF NOT EXISTS public.snipe
(
    id bigint NOT NULL DEFAULT nextval('snipe_id_seq'::regclass),
    guild_id bigint NOT NULL,
    deleted_msg_author text COLLATE pg_catalog."default",
    deleted_msg_author_id bigint,
    deleted_msg_content text COLLATE pg_catalog."default",
    deleted_msg_channel_id bigint,
    deleted_msg_created_at timestamp with time zone,
    edited_msg_author text COLLATE pg_catalog."default",
    edited_msg_author_id bigint,
    pre_edit_content text COLLATE pg_catalog."default",
    post_edit_content text COLLATE pg_catalog."default",
    edited_msg_channel_id bigint,
    pre_created_at timestamp with time zone,
    post_edited_at timestamp with time zone,
    jump_url text COLLATE pg_catalog."default",
    CONSTRAINT snipe_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.snipe
    OWNER to "AV";

COMMENT ON TABLE public.snipe
    IS 'per guild deleted and edited messages stored here';