# -*-coding:utf-8 -*-
import json

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .paginations import CustomPageNumberPagination


# 继承APIView
class APIBaseView(APIView):
    json_content_type = {'content_type': 'application/json'}

    def render_to_json_response(self, status=0, msg=u'成功', data={}, status_code=200):
        context = {}
        context.update(status=status, message=msg, data=data)  # 前端规范为 msg==>message

        return HttpResponse(json.dumps(context), content_type=self.json_content_type, status=status_code)


# 继承ModelViewSet, 有数据库的Model
class BaseViewSet(ModelViewSet):
    pagination_class = CustomPageNumberPagination  # 分页器
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)  # 过滤器
    json_content_type = {'content_type': 'application/json'}  # 返回给前端的数据，转化为json

    def get_object(self):
        """获取实例object"""
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def list(self, request, *args, **kwargs):
        """
        群查：过滤字段 ?id=
             分页 ?page=&page_size
        """
        queryset = self.filter_queryset(self.get_queryset())

        # 存在分页，?page=2&page_size=1  序列化分页的数据 page
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # 否则，序列化全部数据 queryset
        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """单查 1个"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.render_to_json_response(data=serializer.data)

    # def create(self, request, *args, **kwargs):
    #     """单增， 1个"""
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     return self.render_to_json_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """群增, 兼容单增"""
        request_data = request.data
        many = False
        if isinstance(request_data, dict):
            pass
        elif isinstance(request_data, list):
            many = True
        else:
            return self.render_to_json_response(status=1, msg="数据格式有误", status_code=404)

        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return self.render_to_json_response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        """
        单更新，整体or局部，1个
        put /entity/{pk}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # 设置为部分修改partial
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.render_to_json_response(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        单删  1个
        delete /entity/{pk}/
        """
        instance = self.get_object()
        instance.is_deleted = True  # 逻辑删除
        instance.save()
        return self.render_to_json_response(msg='删除成功')

    def delete(self, request, *args, **kwargs):
        """
        群删  {"ids":[1,2,3]}
        delete   /entity/
        """
        ids = request.data.get('ids')
        if not ids and not isinstance(ids, list):
            return self.render_to_json_response(status=1, msg='请输入参数ids, 类型list')
        try:
            update_rows = self.get_queryset().filter(id__in=ids, is_deleted=False).update(is_deleted=True)
        except Exception as e:
            return self.render_to_json_response(status=1, msg='批量删除失败:%s' % e)
        return self.render_to_json_response(msg='批量删除成功:%s条' % update_rows)

    def render_to_json_response(self, status=0, msg=u'成功', data={}, status_code=200):
        """返回提示, 可以定制状态码！"""
        context = {}
        context.update(status=status, message=msg, data=data)  # 前端规范为 msg==>message

        return HttpResponse(json.dumps(context), content_type=self.json_content_type, status=status_code)