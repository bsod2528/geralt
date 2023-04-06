-- Table: public.afk

-- DROP TABLE IF EXISTS public.afk;

CREATE TABLE IF NOT EXISTS public.afk
(
    "user_Id" bigint NOT NULL,
    reason text COLLATE pg_catalog."default",
    queried_at timestamp with time zone,
    CONSTRAINT afk_pkey PRIMARY KEY ("user_Id")
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.afk
    OWNER to av;

-- -- -- -- -- --

-- Table: public.avatar_history

-- DROP TABLE IF EXISTS public.avatar_history;

CREATE TABLE IF NOT EXISTS public.avatar_history
(
    user_id bigint,
    avatar_url text COLLATE pg_catalog."default",
    changed_at timestamp with time zone,
    format text COLLATE pg_catalog."default",
    avatar_bytes bytea
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.avatar_history
    OWNER to av;

-- -- -- -- -- --

-- Table: public.blacklist

-- DROP TABLE IF EXISTS public.blacklist;

CREATE TABLE IF NOT EXISTS public.blacklist
(
    snowflake_id bigint NOT NULL,
    object text COLLATE pg_catalog."default",
    reason text COLLATE pg_catalog."default",
    queried_at timestamp with time zone,
    jump_url text COLLATE pg_catalog."default",
    CONSTRAINT blacklist_pkey PRIMARY KEY (snowflake_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.blacklist
    OWNER to av;

-- -- -- -- -- --

-- Table: public.channel_lock

-- DROP TABLE IF EXISTS public.channel_lock;

CREATE TABLE IF NOT EXISTS public.channel_lock
(
    object_it bigint NOT NULL,
    channel_id bigint,
    guild_id bigint,
    object_type text COLLATE pg_catalog."default",
    queried_at timestamp with time zone,
    CONSTRAINT channel_lock_pkey PRIMARY KEY (object_it)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.channel_lock
    OWNER to av;

-- -- -- -- -- --

-- Table: public.click_global

-- DROP TABLE IF EXISTS public.click_global;

CREATE TABLE IF NOT EXISTS public.click_global
(
    player_id bigint NOT NULL,
    clicks bigint DEFAULT '0'::bigint,
    CONSTRAINT click_global_pkey PRIMARY KEY (player_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.click_global
    OWNER to av;

-- -- -- -- -- --

-- Table: public.click_guild

-- DROP TABLE IF EXISTS public.click_guild;

CREATE TABLE IF NOT EXISTS public.click_guild
(
    guild_id bigint NOT NULL,
    player_id bigint,
    clicks bigint DEFAULT '0'::bigint,
    CONSTRAINT click_guild_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.click_guild
    OWNER to av;

-- -- -- -- -- --

-- Table: public.discriminator_history

-- DROP TABLE IF EXISTS public.discriminator_history;

CREATE TABLE IF NOT EXISTS public.discriminator_history
(
    user_id bigint,
    discriminator text COLLATE pg_catalog."default",
    changed_at timestamp with time zone
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.discriminator_history
    OWNER to av;

-- -- -- -- -- --

-- Table: public.guild_settings

-- DROP TABLE IF EXISTS public.guild_settings;

CREATE TABLE IF NOT EXISTS public.guild_settings
(
    guild_id bigint NOT NULL,
    convert_url_to_webhook boolean,
    snipe boolean,
    CONSTRAINT guild_settings_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.guild_settings
    OWNER to av;

-- -- -- -- -- --

-- Table: public.highlight_blocked

-- DROP TABLE IF EXISTS public.highlight_blocked;

CREATE TABLE IF NOT EXISTS public.highlight_blocked
(
    user_id bigint NOT NULL,
    guild_id bigint NOT NULL,
    object_id bigint NOT NULL,
    object_type text COLLATE pg_catalog."default",
    queried_at timestamp with time zone,
    CONSTRAINT highlight_blocked_pkey1 PRIMARY KEY (user_id, guild_id, object_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.highlight_blocked
    OWNER to av;

-- -- -- -- -- --

-- Table: public.highlight

-- DROP TABLE IF EXISTS public.highlight;

CREATE TABLE IF NOT EXISTS public.highlight
(
    user_id bigint NOT NULL,
    guild_id bigint NOT NULL,
    trigger text COLLATE pg_catalog."default" NOT NULL,
    queried_at timestamp with time zone,
    CONSTRAINT highlight_pkey PRIMARY KEY (trigger, guild_id, user_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.highlight
    OWNER to av;

-- -- -- -- -- --

-- Table: public.meta

-- DROP TABLE IF EXISTS public.meta;

CREATE TABLE IF NOT EXISTS public.meta
(
    guild_id bigint NOT NULL,
    command_name text COLLATE pg_catalog."default" NOT NULL,
    uses bigint DEFAULT '0'::bigint,
    invoked_at timestamp with time zone,
    CONSTRAINT meta_pkey PRIMARY KEY (guild_id, command_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.meta
    OWNER to av;

-- -- -- -- -- --

-- Table: public.prefix

-- DROP TABLE IF EXISTS public.prefix;

CREATE TABLE IF NOT EXISTS public.prefix
(
    guild_id bigint NOT NULL,
    prefixes text[] COLLATE pg_catalog."default",
    CONSTRAINT prefix_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.prefix
    OWNER to av;

-- -- -- -- -- --

-- Table: public.snipe_delete

-- DROP TABLE IF EXISTS public.snipe_delete;

CREATE TABLE IF NOT EXISTS public.snipe_delete
(
    guild_id bigint,
    d_m_c_id bigint,
    d_m_a_id bigint,
    d_m_cc text COLLATE pg_catalog."default",
    d_m_ts timestamp with time zone,
    embeds jsonb[],
    attachment_names text[] COLLATE pg_catalog."default",
    attachment_bytes bytea[],
    attachment_urls text[] COLLATE pg_catalog."default",
    attachment_exts text[] COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.snipe_delete
    OWNER to av;

COMMENT ON TABLE public.snipe_delete
    IS 'd = deleted
e = edited
m = message
c = channel
a = author

cc = content
ts = timestamp
pr = pre - edit
po = post_edit';

-- -- -- -- -- --

-- Table: public.snipe_edit

-- DROP TABLE IF EXISTS public.snipe_edit;

CREATE TABLE IF NOT EXISTS public.snipe_edit
(
    guild_id bigint,
    pre_c_id bigint,
    pre_m_id bigint,
    pre_m_a_id bigint,
    pre_cc text COLLATE pg_catalog."default",
    pre_ts timestamp with time zone,
    post_cc text COLLATE pg_catalog."default",
    post_ts timestamp with time zone,
    pre_at_exts text[] COLLATE pg_catalog."default",
    pre_at_urls text[] COLLATE pg_catalog."default",
    pre_at_names text[] COLLATE pg_catalog."default",
    pre_at_bytes bytea[],
    post_at_exts text[] COLLATE pg_catalog."default",
    post_at_urls text[] COLLATE pg_catalog."default",
    post_at_names text[] COLLATE pg_catalog."default",
    post_at_bytes bytea[],
    jump_url text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.snipe_edit
    OWNER to postgres;

COMMENT ON TABLE public.snipe_edit
    IS 'd = deleted
e = edited
m = message
c = channel
a = author

at = attachment
cc = content
ts = timestamp
pr = pre - edit
po = post_edit
eb = embed';

-- -- -- -- -- --

-- Table: public.tags

-- DROP TABLE IF EXISTS public.tags;

CREATE TABLE IF NOT EXISTS public.tags
(
    tag_id bigint NOT NULL DEFAULT 'nextval('tags_tag_id_seq'::regclass)',
    guild_id bigint NOT NULL,
    tag_name text COLLATE pg_catalog."default" NOT NULL,
    content text COLLATE pg_catalog."default",
    author_id bigint,
    jump_url text COLLATE pg_catalog."default",
    uses bigint DEFAULT '0'::bigint,
    created_at timestamp with time zone,
    CONSTRAINT tags_pkey PRIMARY KEY (guild_id, tag_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tags
    OWNER to av;

-- -- -- -- -- --

-- Table: public.ticket_init

-- DROP TABLE IF EXISTS public.ticket_init;

CREATE TABLE IF NOT EXISTS public.ticket_init
(
    id bigint NOT NULL DEFAULT 'nextval('ticket_init_id_seq'::regclass)',
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
    OWNER to av;

-- -- -- -- -- --

-- Table: public.ticket_kernel

-- DROP TABLE IF EXISTS public.ticket_kernel;

CREATE TABLE IF NOT EXISTS public.ticket_kernel
(
    ticket_id bigint NOT NULL DEFAULT 'nextval('ticket_kernel_ticket_id_seq'::regclass)',
    guild_id bigint,
    invoker_id bigint,
    channel_id bigint,
    CONSTRAINT ticket_kernel_pkey PRIMARY KEY (ticket_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.ticket_kernel
    OWNER to av;

-- -- -- -- -- --

-- Table: public.todo

-- DROP TABLE IF EXISTS public.todo;

CREATE TABLE IF NOT EXISTS public.todo
(
    task_id bigint NOT NULL DEFAULT 'nextval('todo_task_id_seq'::regclass)',
    user_id bigint,
    task text COLLATE pg_catalog."default",
    created_at timestamp with time zone,
    jump_url text COLLATE pg_catalog."default",
    CONSTRAINT todo_pkey PRIMARY KEY (task_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.todo
    OWNER to av;

-- -- -- -- -- --

-- Table: public.user_settings

-- DROP TABLE IF EXISTS public.user_settings;

CREATE TABLE IF NOT EXISTS public.user_settings
(
    user_id bigint NOT NULL,
    avatar boolean,
    username boolean,
    discriminator boolean,
    CONSTRAINT user_settings_pkey PRIMARY KEY (user_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_settings
    OWNER to av;

-- -- -- -- -- --

-- Table: public.username_history

-- DROP TABLE IF EXISTS public.username_history;

CREATE TABLE IF NOT EXISTS public.username_history
(
    user_id bigint,
    user_name text COLLATE pg_catalog."default",
    changed_at timestamp with time zone
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.username_history
    OWNER to av;

-- -- -- -- -- --

-- Table: public.verification

-- DROP TABLE IF EXISTS public.verification;

CREATE TABLE IF NOT EXISTS public.verification
(
    guild_id bigint NOT NULL,
    question text COLLATE pg_catalog."default",
    answer text COLLATE pg_catalog."default",
    role_id text COLLATE pg_catalog."default",
    channel_id text COLLATE pg_catalog."default",
    message_id text COLLATE pg_catalog."default",
    CONSTRAINT verification_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.verification
    OWNER to av;

-- -- -- -- -- --