-- Table: public.tags
-- DROP TABLE IF EXISTS public.tags;

CREATE TABLE IF NOT EXISTS public.tags
(
    id bigint NOT NULL DEFAULT nextval('tags_id_seq1'::regclass),
    name text COLLATE pg_catalog."default" NOT NULL,
    content text COLLATE pg_catalog."default" NOT NULL,
    author_id bigint NOT NULL,
    author_name text COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    created_on timestamp with time zone NOT NULL,
    jump_url text COLLATE pg_catalog."default" NOT NULL,
    uses bigint DEFAULT 0,
    alias text COLLATE pg_catalog."default",
    CONSTRAINT tags_pkey1 PRIMARY KEY (name, guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tags
    OWNER to "AV";

COMMENT ON TABLE public.tags
    IS 'tags for each guild';