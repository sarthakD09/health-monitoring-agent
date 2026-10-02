from app.models import Context, Observation


def build_context(observation: Observation) -> Context:
    missing_fields: list[str] = []

    if observation.activity is None:
        missing_fields.append("activity")

    return Context(
        activity=observation.activity,
        is_available=not missing_fields,
        missing_fields=missing_fields,
    )
