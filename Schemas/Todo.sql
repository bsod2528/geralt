-- Table: public.todo
-- DROP TABLE IF EXISTS public.todo;

CREATE TABLE IF NOT EXISTS public.todo
(
    task_id bigint NOT NULL DEFAULT nextval('todo_task_id_seq'::regclass),
    user_name text COLLATE pg_catalog."default" NOT NULL,
    user_id bigint NOT NULL,
    discriminator text COLLATE pg_catalog."default" NOT NULL,
    task text COLLATE pg_catalog."default" NOT NULL,
    task_created_at timestamp with time zone NOT NULL,
    url text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT todo_pkey PRIMARY KEY (task_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.todo
    OWNER to "AV";

COMMENT ON TABLE public.todo
    IS 'global todo table for each user';