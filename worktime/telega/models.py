from django.db import models
from django.utils.translation import gettext_lazy as _


class Worker(models.Model):
    POSITION_CHOICES = [
        (_('модель'), _('Модель')),
        (_('оператор'), _('Оператор'))
    ]

    REST_DAY = [
        (0, _('Понедельник')),
        (1, _('Вторник')),
        (2, _('Среда')),
        (3, _('Четверг')),
        (4, _('Пятница')),
        (6, _('Воскресенье')),
    ]

    name = models.CharField(_('имя'), max_length=50)
    username = models.CharField(_('никнейм'), max_length=60)
    position = models.CharField(_('позиция'), max_length=30, choices=POSITION_CHOICES)
    location = models.CharField(_('локация'), max_length=100)
    work_start_time = models.TimeField(_('начало смены'))
    rest_day = models.PositiveSmallIntegerField(_('выходной'), choices=REST_DAY, null=True, blank=True)
    active = models.BooleanField(_('активен'), default=False)

    class Meta:
        verbose_name = _('работник')
        verbose_name_plural = _('работники')
