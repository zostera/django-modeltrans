from django.contrib.auth import get_user_model


def disable_admin_login():
    '''
    Disable admin login, but allow editing.

    amended from: https://stackoverflow.com/a/40008282/517560
    '''
    User = get_user_model()

    user, created = User.objects.update_or_create(
        id=1,
        defaults=dict(
            first_name='Default Admin',
            last_name='User',
            is_superuser=True,
            is_active=True,
            is_staff=True
        )
    )

    def no_login_has_permission(request):
        setattr(request, 'user', user)

        return True

    return no_login_has_permission
