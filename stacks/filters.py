import django_filters
from .models import Stack, UserStack


class StackFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        help_text='Filtra stacks pelo nome. Ex: "Python" ou "java"',
    )

    class Meta:
        model = Stack
        fields = ["name"]


class UserStackFilter(django_filters.FilterSet):
    proficiency_level = django_filters.ChoiceFilter(
        choices=UserStack.PROFICIENCY_LEVELS,
        help_text='Filtra por nível de proficiência. Ex: "BEG" para iniciante',
    )

    # Filtro para anos de experiência com comparações
    years_of_experience = django_filters.NumberFilter(
        help_text="Filtra por anos exatos de experiência"
    )
    years_of_experience_gte = django_filters.NumberFilter(
        field_name="years_of_experience",
        lookup_expr="gte",  # greater than or equal (maior ou igual)
        help_text="Filtra por anos de experiência maior ou igual. Ex: 5 para 5+ anos",
    )
    years_of_experience_lte = django_filters.NumberFilter(
        field_name="years_of_experience",
        lookup_expr="lte",  # less than or equal (menor ou igual)
        help_text="Filtra por anos de experiência menor ou igual",
    )

    # Filtro para o nome da stack relacionada
    stack_name = django_filters.CharFilter(
        field_name="stack__name",
        lookup_expr="icontains",
        help_text='Filtra pela tecnologia. Ex: "Python" ou "React"',
    )

    class Meta:
        model = UserStack
        fields = ["proficiency_level", "years_of_experience", "stack_name"]
