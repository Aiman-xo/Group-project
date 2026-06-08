from pydantic import BaseModel,EmailStr

class CompanyRegister(BaseModel):

    email: EmailStr
    company_name: str
    website_link: str | None = None
    industry: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email:EmailStr
    password:str

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendOTPRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyForgotPasswordOTPRequest(BaseModel):
    email:EmailStr
    otp:str

class ResetPasswordRequest(BaseModel):
    email:EmailStr
    new_password:str
    confirm_password: str