from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _


class CommentLikeAbstractModel(models.Model):
    """
    An abstract base class that any custom comment like models probably should
    subclass.
    """

    date_created = models.DateTimeField(_('date created'), default=timezone.now)
    date_updated = models.DateTimeField(_('date updated'), auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, null=False)
    # comment -- Required field

    class Meta:
        abstract = True
        unique_together = ('user', 'comment',)

    @classmethod
    def count_likes(cls, comment, *args):
        return cls._default_manager.filter(comment=comment).count()

    @classmethod
    def has_liked(cls, user, comment, *args):
        return cls._default_manager.filter(user=user, comment=comment).exists()

    @classmethod
    def like(cls, user, comment, *args):
        if cls._default_manager.filter(user=user, comment=comment).exists():
            return cls._default_manager.get(user=user, comment=comment)
        return cls._default_manager.create(user=user, comment=comment)

    @classmethod
    def unlike(cls, user, comment, *args):
        if cls._default_manager.filter(user=user, comment=comment).exists():
            cls._default_manager.filter(user=user, comment=comment).delete()
            return True
        return False
