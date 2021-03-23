create table teams (
    id character varying(120) not null primary key,
    name character varying(120) not null,
    bot_user_id character varying(120) not null,
    bot_access_token character varying(256) not null,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

create index idx_teams_id on teams using btree (id);
create index idx_teams_bot_access_token on teams using btree (bot_access_token);

----------------------------------------------------------------------------------------

create table users (
    id serial primary key,
    slack_user_id character varying(120) not null unique,
    slack_team_id character varying(120) not null references teams(id) on delete cascade,
    slack_dm_channel_id character varying(120) not null unique,
    email character varying(120) not null,
    fyle_refresh_token text not null,
    fyle_employee_id character varying(120) not null unique,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

create index idx_users_slack_user_id on users using btree (slack_user_id);
create index idx_users_slack_team_id on users using btree (slack_team_id);
create index idx_users_slack_dm_channel_id on users using btree (slack_dm_channel_id);
create index idx_users_fyle_refresh_token on users using btree (fyle_refresh_token);

-----------------------------------------------------------------------------------------

create table report_polling_details (
    id serial primary key,
    user_id character varying(120) not null references users(slack_user_id) on delete cascade,
    last_successful_poll_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

create index idx_report_polling_details_user_id on report_polling_details using btree (user_id);
create index idx_report_polling_details_last_successful_poll_at on report_polling_details using btree (last_successful_poll_at);
