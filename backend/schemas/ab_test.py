from pydantic import BaseModel


class ABTestResponse(BaseModel):
    group_a: str
    group_b: str
    n_a: int
    n_b: int
    conversions_a: int
    conversions_b: int
    conversion_a: float
    conversion_b: float
    absolute_diff: float
    relative_uplift: float
    z_statistic: float
    p_value: float
    significant: bool
