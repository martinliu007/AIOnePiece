from django.db import models

class BaseModel(models.Model):
    """基表"""
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name="是否删除")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True