from pydantic import BaseModel, Field, ConfigDict


class SearchCityModel(BaseModel):
    id: str
    label: str
    city: str
    state: str
    country: str


class SearchRequestModel(BaseModel):
    model_config = ConfigDict(validate_by_name=True)
    from_: SearchCityModel = Field(..., alias="from")
    to: SearchCityModel
