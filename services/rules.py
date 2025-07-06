from constants import Action, Resource, Service
from models import Rules
from pydantic.dataclasses import dataclass
from schemas import Rule
from services.utils import get_all_rules


@dataclass
class AnonymousRules:
    rules: list[Rule] = (
        Rule(
            service=Service.async_api,
            resource=Resource.free_movie,
            action=Action.read,
        ),
        Rule(
            service=Service.async_api,
            resource=Resource.other,
            action=Action.read,
        ),
    )


@dataclass
class UserRules(AnonymousRules):
    rules: list[Rule] = (
        *AnonymousRules.rules,
        Rule(
            service=Service.async_api,
            resource=Resource.users_movie,
            action=Action.read,
        ),
    )


@dataclass
class SubscriptionRules(UserRules):
    rules: list[Rule] = (
        *UserRules.rules,
        Rule(
            service=Service.async_api,
            resource=Resource.subscription_movie,
            action=Action.read,
        ),
    )


@dataclass
class AdminRules:
    """Админ имеет права на все."""

    rules: list[Rule] = get_all_rules()


rules = {
    Rules.anonymous_rules: AnonymousRules,
    Rules.user_rules: UserRules,
    Rules.subscription_rules: SubscriptionRules,
    Rules.admin_rules: AdminRules,
}
