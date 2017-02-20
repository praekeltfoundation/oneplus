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

    def count_likes(self, comment):
        return self._default_manager.filter(comment=comment).count()

    def has_liked(self, user, comment):
        return self._default_manager.filter(user=user, comment=comment).exists()

    def like(self, user, comment):
        if self._default_manager.filter(user=user, comment=comment).exists():
            return self._default_manager.get(user=user, comment=comment)
        return self._default_manager.create(user=user, comment=comment)

    def unlike(self, user, comment):
        if self._default_manager.filter(user=user, comment=comment).exists():
            self._default_manager.filter(user=user, comment=comment).delete()
            return True
        return False
