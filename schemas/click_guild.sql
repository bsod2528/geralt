-- Table: public.click_guild
-- DROP TABLE IF EXISTS public.click_guild;

CREATE TABLE IF NOT EXISTS public.click_guild
(
    guild_id bigint NOT NULL,
    player_id bigint NOT NULL,
    clicks bigint DEFAULT 0,
    player_name text COLLATE pg_catalog."default",
    CONSTRAINT guild_click_pkey PRIMARY KEY (guild_id, player_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.click_guild
    OWNER to "AV";

COMMENT ON TABLE public.click_guild
    IS 'stores info on click game for a guild';