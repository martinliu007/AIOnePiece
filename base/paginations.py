# -*-coding:utf-8 -*-

from collections import OrderedDict

from django.utils import six
from django.core.paginator import InvalidPage
from rest_framework.views import Response
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """分页组件，重写PageNumberPagination"""
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    page_size = 15
    page_number = 1

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)

        # 当page_size == -1, 返回所有data，
        if self.page_size == -1:
            self.count = self.get_count(queryset)  # len(queryset) or queryset.count()
            return list(queryset)

        paginator = self.django_paginator_class(queryset, self.page_size)  # 继承django的paginator

        self.page_number = request.query_params.get(self.page_query_param, 1)  # request.query_params.get('page')
        if self.page_number in self.last_page_strings:
            self.page_number = paginator.num_pages

        try:
            self.page = paginator.page(self.page_number)
        except InvalidPage as exc:
            # 方式1：# 前端异常 {"detail": "Invalid page."}
            msg = self.invalid_page_message.format(
                page_number=self.page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

            # 方式2：超过最大page，只取最后一页的数据
            # self.page_number = ceil(len(queryset) / self.page_size)
            # self.page = paginator.page(self.page_number)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.     #  可浏览的API，应该显示分页控件。
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        if self.page_size == -1:  # page_size=1 重写定义
            return Response(OrderedDict([
                ('status', 0),
                ('count', self.count),  # queryset的全部总数
                ('page', self.page_number),
                ('page_size', self.page_size),
                ('data', data)
            ]))
        return Response(OrderedDict([
            ('status', 0),
            ('count', self.page.paginator.count),
            ('page', self.page_number),
            ('page_size', self.page_size),
            ('data', data)
        ]))

    def get_page_size(self, request):  # request.query_params.get('page_size')

        page_size = request.query_params[self.page_size_query_param] \
            if request.query_params.get(self.page_size_query_param) else self.page_size

        # 转换为int类型
        try:
            page_size = int(page_size)
        except Exception as e:
            page_size = self.page_size
        return page_size

    def get_count(self, queryset):
        """
        Determine an object count, supporting either querysets or regular lists.
        定一个对象计数，支持查询集或常规列表
        """
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)