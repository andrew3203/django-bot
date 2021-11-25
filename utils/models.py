from django.db import models
from typing import Union, Optional, Tuple, Any
from django.utils.translation import ugettext_lazy as _



nb = dict(null=True, blank=True)


class CreateTracker(models.Model):
    created_at = models.DateTimeField(_('Дата регистрации'), auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class CreateUpdateTracker(CreateTracker):
    updated_at = models.DateTimeField(_('Последняя активнсоть'),auto_now=True)

    class Meta(CreateTracker.Meta):
        abstract = True


class HelpContext(object):

    def __init__(self, role: str, 
        user_id: int,
        message_id: int = None,
        action: str = 'send', 
        to_top: bool = False, 
        keywords: dict = None, 
        navigation: dict = None, 
        profile_status: str = None,
        jobs_names: list = []
    ) -> None:
        super().__init__()
        
        self.user_id = user_id
        self.action = action
        self.to_top = to_top
        self.message_id = message_id
        self.navigation = navigation
        self.keywords = keywords
        self.profile_status = profile_status
        self.role: str = role
        self.jobs_names = jobs_names

        


