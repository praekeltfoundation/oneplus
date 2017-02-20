from django.db import models
from django.conf import settings


class CommentLikeAbstractModel(models.Model):
    """
    An abstract base class that any custom comment models probably should
    subclass.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, null=False, related_name="like_user")
    # comment -- Required field

    class Meta:
        abstract = True
        unique_together = ('user', 'comment',)

    def count_likes(self, comment):
        return self._default_manager.filter(comment=comment).count()

    def like(self, user, comment):
        if self._default_manager.filter(user=user, comment=comment).exists():
            return self._default_manager.get(user=user, comment=comment)
        return self._default_manager.create(user=user, comment=comment)

    def unlike(self, user, comment):
        if self._default_manager.filter(user=user, comment=comment).exists():
            self._default_manager.filter(user=user, comment=comment).delete()
            return True
        return False
