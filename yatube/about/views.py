from django.views.generic.base import TemplateView


class AboutPage(TemplateView):
    template_name = 'about/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Очень простая страница'
        context['just_text'] = ('На создание этой страницы '
                                'у меня ушло пять минут! Ай да я.')
        return context


class TechPage(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Очень не простая страница'
        context['just_text'] = ('На создание этой страницы '
                                'у меня ушло не пять минут! Ай да я.')
        return context
