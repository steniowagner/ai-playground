from .anthropic import create_anthropic_model
from .schema import Model, ModelTypes


def create_model(model_type: ModelTypes, *, model_name: str | None = None) -> Model:
    match model_type:
        case "anthropic":
            return create_anthropic_model(model_name)
        case _:
            pass
