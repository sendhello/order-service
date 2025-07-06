from constants import Action, Resource, Service
from schemas import Rule


def get_all_rules() -> tuple:
    rules = []
    for service in Service:
        for resource in Resource:
            for action in Action:
                rules.append(
                    Rule(
                        service=service,
                        resource=resource,
                        action=action,
                    )
                )

    return tuple(rules)
