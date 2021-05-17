-- Script to add notification preference for existing users

-- Usage
-- select fn_add_notification_preferences_to_existing_users(array['APPROVER_REPORT_APPROVAL']);
-- select fn_add_notification_preferences_to_existing_users(array['APPROVER_REPORT_APPROVAL', 'FYLER_REPORT_APPROVED']);


-- This function adds the notification types passed in parameter to all the users
-- If a user doesn't have that notification type it will be added for that user
-- If the passed notification types already exists for a user it won't be added for that user.

create or replace function fn_add_notification_preferences_to_existing_users(notification_types text[])
returns void as $body$
declare
    _notification_type text;
begin
    foreach _notification_type in array notification_types
    loop
        insert into notification_preferences (
            slack_user_id,
            notification_type,
            is_enabled
        ) select slack_user_id,
        _notification_type as notification_type,
        true as is_enabled
        from users
        on conflict (slack_user_id, notification_type) do nothing;
    end loop;
end;
$body$ language plpgsql strict;