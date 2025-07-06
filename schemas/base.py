from pydantic import ConfigDict, BaseModel


class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True)
