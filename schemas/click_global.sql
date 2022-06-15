-- Table: public.click_global
-- DROP TABLE IF EXISTS public.click_global;

CREATE TABLE IF NOT EXISTS public.click_global
(
    player_id bigint NOT NULL,
    clicks bigint DEFAULT 0,
    player_name text COLLATE pg_catalog."default",
    player_pfp text COLLATE pg_catalog."default",
    CONSTRAINT click_global_pkey PRIMARY KEY (player_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.click_global
    OWNER to "AV";

COMMENT ON TABLE public.click_global
    IS 'global leaderboard for click';