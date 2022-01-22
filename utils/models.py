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

    def __name__(self):
        return 'HelpContext'

    def copy(self):
        return HelpContext(**self.__dict__.copy())

    def __init__(self, role: str, 
        user_id: int,
        message_id: int = None,
        action: str = 'send', 
        keywords: dict = None, 
        navigation: dict = None, 
        profile_status: str = None,
        prev_answer_type: str = None,
        question: dict = {},
    ) -> None:
        super().__init__()
        
        self.user_id = user_id
        self.__dict__.update({'user_id': user_id})
        self.action = action
        self.__dict__.update({'action': action})
        self.message_id = message_id
        self.__dict__.update({'message_id': message_id})
        self.navigation = navigation
        self.__dict__.update({'navigation': navigation})
        self.keywords = keywords
        self.__dict__.update({'keywords': keywords})
        self.profile_status = profile_status
        self.__dict__.update({'profile_status': profile_status})
        self.role = role
        self.__dict__.update({'role': role})
        self.prev_answer_type = prev_answer_type
        self.__dict__.update({'prev_answer_type': prev_answer_type})
        self.question = question
        self.__dict__.update({'question': question})

        


