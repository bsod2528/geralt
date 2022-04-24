---

-- Database: Geralt
-- DROP DATABASE IF EXISTS "Geralt";

CREATE DATABASE "Geralt"
    WITH 
    OWNER = "AV"
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_India.1252'
    LC_CTYPE = 'English_India.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE "Geralt"
    IS 'For Geralt - Discord Bot';

---
---

-- Table: public.custom_prefix
-- DROP TABLE IF EXISTS public.custom_prefix;

CREATE TABLE IF NOT EXISTS public.custom_prefix
(
    guild_prefix text COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    guild_name text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT custom_prefix_pkey PRIMARY KEY (guild_id),
    CONSTRAINT guild_id UNIQUE (guild_id, guild_prefix),
    CONSTRAINT guild_prefix UNIQUE (guild_prefix, guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.custom_prefix
    OWNER to postgres;

---
---

-- Table: public.guild_info
-- DROP TABLE IF EXISTS public.guild_info;

CREATE TABLE IF NOT EXISTS public.guild_info
(
    id bigint NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    owner_id bigint NOT NULL,
    CONSTRAINT guild_info_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.guild_info
    OWNER to "AV";

COMMENT ON TABLE public.guild_info
    IS 'Logs new guilds information upon joining';

---
---

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
    IS 'Table for Todo command.';

 Table: public.todo

---
---

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
    CONSTRAINT tags_pkey1 PRIMARY KEY (name, guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tags
    OWNER to "AV";

COMMENT ON TABLE public.tags
    IS 'Table for tags';

    