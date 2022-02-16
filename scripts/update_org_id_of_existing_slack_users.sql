create temp table slack_users_org_id_list(fyle_user_id text, fyle_org_id text);

\copy slack_users_org_id_list from 'slack_users_org_id_list.csv' csv header;

update users u set fyle_org_id = s.fyle_org_id from slack_users_org_id_list s where u.fyle_user_id = s.fyle_user_id;