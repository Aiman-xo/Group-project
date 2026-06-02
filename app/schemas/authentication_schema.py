from pydantic import BaseModel,EmailStr

class CompanyRegister(BaseModel):

    email: EmailStr
    company_name: str
    website_link: str | None = None
    industry: str
    password: str


class LoginRequest(BaseModel):
    email:EmailStr
    password:str