import django_filters

from projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    """
    Filtros para o modelo Project.
    Permite filtrar por nome (contém), Tech Leader, status e intervalos de datas.
    """

    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        help_text="Filtra projetos que contêm o texto especificado no nome, sem distinção entre maiúsculas e minúsculas",
    )
    tech_leader_email = django_filters.CharFilter(
        field_name="tech_leader__email",
        lookup_expr="icontains",
        help_text="Filtra projetos pelo email do Tech Leader, permitindo busca parcial",
    )
    tech_leader = django_filters.NumberFilter(
        field_name="tech_leader__id",
        help_text="Filtra projetos pelo ID exato do Tech Leader",
    )
    stack_name = django_filters.CharFilter(
        field_name="stacks__name",
        lookup_expr="icontains",
        help_text="Filtra projetos que utilizam stacks com o nome especificado, permitindo busca parcial",
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=Project._meta.get_field("status").choices,
        help_text="Filtra projetos pelo status exato (PLANNING, IN_PROGRESS, COMPLETED, ON_HOLD)",
    )
    start_date_after = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        help_text="Filtra projetos com data de início igual ou posterior à data especificada (formato: YYYY-MM-DD)",
    )
    start_date_before = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="lte",
        help_text="Filtra projetos com data de início igual ou anterior à data especificada (formato: YYYY-MM-DD)",
    )
    end_date_after = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="gte",
        help_text="Filtra projetos com data de término igual ou posterior à data especificada (formato: YYYY-MM-DD)",
    )
    end_date_before = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        help_text="Filtra projetos com data de término igual ou anterior à data especificada (formato: YYYY-MM-DD)",
    )


class ProjectDeveloperFilter(django_filters.FilterSet):
    """
    Filtros para o modelo ProjectDeveloper.
    Permite filtrar por projeto, desenvolvedor, stack e intervalos de datas.
    """

    project = django_filters.NumberFilter(
        field_name="project__id", help_text="Filtra alocações pelo ID exato do projeto"
    )
    developer = django_filters.NumberFilter(
        field_name="developer__id",
        help_text="Filtra alocações pelo ID exato do desenvolvedor",
    )
    developer_email = django_filters.CharFilter(
        field_name="developer__email",
        lookup_expr="icontains",
        help_text="Filtra alocações pelo email do desenvolvedor, permitindo busca parcial",
    )
    stack = django_filters.NumberFilter(
        field_name="stack__id", help_text="Filtra alocações pelo ID exato da stack"
    )
    start_date_after = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        help_text="Filtra alocações com data de início igual ou posterior à data especificada (formato: YYYY-MM-DD)",
    )
    start_date_before = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="lte",
        help_text="Filtra alocações com data de início igual ou anterior à data especificada (formato: YYYY-MM-DD)",
    )
    end_date_after = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="gte",
        help_text="Filtra alocações com data de término igual ou posterior à data especificada (formato: YYYY-MM-DD)",
    )
    end_date_before = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        help_text="Filtra alocações com data de término igual ou anterior à data especificada (formato: YYYY-MM-DD)",
    )


class ProjectStackFilter(django_filters.FilterSet):
    """
    Filtros para o modelo ProjectStack.
    Permite filtrar por projeto, stack e número de desenvolvedores necessários.
    """

    project = django_filters.NumberFilter(
        field_name="project__id",
        help_text="Filtra requisitos de stack pelo ID exato do projeto",
    )
    stack = django_filters.NumberFilter(
        field_name="stack__id", help_text="Filtra requisitos pelo ID exato da stack"
    )
    required_developers_min = django_filters.NumberFilter(
        field_name="required_developers",
        lookup_expr="gte",
        help_text="Filtra requisitos que necessitam de um número igual ou maior de desenvolvedores",
    )
    required_developers_max = django_filters.NumberFilter(
        field_name="required_developers",
        lookup_expr="lte",
        help_text="Filtra requisitos que necessitam de um número igual ou menor de desenvolvedores",
    )
