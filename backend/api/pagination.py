from rest_framework.pagination import PageNumberPagination

class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'

    def get_page_size(self, request):
        page_size = request.query_params.get(self.page_size_query_param)
        if page_size is not None:
            try:
                page_size = int(page_size)
                if page_size > 0:
                    return page_size
            except ValueError:
                return(
                    'Не может быть отрицательное число'
                )
        return self.page_size