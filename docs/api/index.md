# API reference

Auto-generated from docstrings via [mkdocstrings](https://mkdocstrings.github.io/).
Scoped to the domain and application layers — the parts of CodePulse with a
stable, framework-agnostic public surface worth documenting as an API.
Infrastructure and presentation classes are covered narratively in
[architecture.md](../architecture.md) and [developer_guide.md](../developer_guide.md)
instead, since their "interface" is mostly Qt/PySide6 signatures already
documented by Qt itself.

## Domain models

::: codepulse.domain.models.profile
::: codepulse.domain.models.stats
::: codepulse.domain.models.streak
::: codepulse.domain.models.contest
::: codepulse.domain.models.daily_challenge
::: codepulse.domain.models.goal
::: codepulse.domain.models.widget
::: codepulse.domain.models.preferences
::: codepulse.domain.models.cache_entry
::: codepulse.domain.models.notification_state

## Domain interfaces

::: codepulse.domain.interfaces.provider
::: codepulse.domain.interfaces.cache_repository
::: codepulse.domain.interfaces.settings_repository
::: codepulse.domain.interfaces.desktop_layout_repository
::: codepulse.domain.interfaces.goal_repository
::: codepulse.domain.interfaces.notification_state_repository
::: codepulse.domain.interfaces.notifier

## Application services

::: codepulse.application.services.stats_service
::: codepulse.application.services.goal_service
::: codepulse.application.services.notification_service
