from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the Accounts app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """Import signals for the Accounts app."""
        import accounts.signals
