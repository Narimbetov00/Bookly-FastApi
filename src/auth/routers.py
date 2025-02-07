from fastapi import APIRouter,Depends,BackgroundTasks
from fastapi.responses import JSONResponse
from .schemas import UserCreateModel,UserModel,UserLoginModel,UserBooksModel,EmailModel,PasswordResetRequestModel,PasswordResetConfirmModel
from .service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from src.db.models import User
from .utils import create_access_token,decode_token,verify_password,create_url_safe_token,decode_url_safe_token,generate_passwd_hash
from datetime import timedelta,datetime
from .dependencies import RefreshTokenBearer,AccessTokenBearer,get_current_user,RoleChecker
from src.db.redis import add_jti_to_blocklist
from src.errors import UserAlreadyExists,UserNotFound,InvalidCredentials,InvalidToken
from src.mail import mail,create_message
from src.config import Config
     

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['admin','User'])
REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/send_mail")
async def send_mail(emails:EmailModel):
    emails = emails.addresses
    
    html="<h1> Welcome to the app </h1>"
    
    message = create_message(
        recipients=emails,
        subject="Welcome",
        body=html
    )
    await mail.send_message(message)
    return {"message":"Email Send Successfully"}

@auth_router.get("/verify/{token}")
async def verify_user_account(token:str,session:AsyncSession=Depends(get_session)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email,session)
        
        if not user:
            raise UserNotFound()
    
        await user_service.update_user(user,{"is_verified":True},session)

        return JSONResponse(content={
            "message":"Successfully verified"
        },status_code=200)
    return JSONResponse(content={
        "message":"Error occured during verification"
    },status_code=400)
@auth_router.post("/signup",
                status_code=201)
async def create_user_account(user_data:UserCreateModel,bg_task:BackgroundTasks,session:AsyncSession=Depends(get_session)):
    email = user_data.email

    user_exists = await user_service.user_exists(email,session)

    if user_exists:
        raise UserAlreadyExists()


    new_user = await user_service.create_user(user_data,session)

    token = create_url_safe_token({"email":email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"

    html_message =f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a>to verify your email</p>
    """
    message = create_message(
        recipients=[email],
        subject="Verify your email",
        body=html_message
    )
    bg_task.add_task(mail.send_message,message)

    return {"message":"Account Created! check email to verify your account",
            "user":new_user}

@auth_router.post("/login")
async def login_users(login_data:UserLoginModel,session:AsyncSession=Depends(get_session)):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email,session)

    if user is not None:
        password_valid = verify_password(password,user.password_hash)
        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email":user.email,
                    "user_uid":str(user.uid),
                    "role":user.role
                }
            )
            refresh_token = create_access_token(
                user_data={
                    "email":user.email,
                    "user_uid":str(user.uid),
                    "role":user.role
                },
                refresh = True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
            )

            return JSONResponse(
                content={
                    "message":"Login successful",
                    "access_token":str(access_token),
                    "refresh_token":str(refresh_token),
                    "user":{
                        "email":str(user.email),
                        "uid":str(user.uid)
                    }
                }
            )

    raise InvalidCredentials()
@auth_router.get("/refresh_token")
async def get_new_access_token(token_details:dict=Depends(RefreshTokenBearer)):

    expiry_timestamp = token_details['exp']
    
    if datetime.fromtimestamp(expiry_timestamp)>datetime.now():
        new_access_token = create_access_token(
            user_data=token_details['user']
        )
        return JSONResponse(
            content={
                "access_token":new_access_token
            })
    raise InvalidToken()

@auth_router.get('/me',response_model=UserBooksModel)
async def get_current_user(user=Depends(get_current_user),_:bool=Depends(role_checker)):
    return user

@auth_router.get('/logout')
async def revooke_token(token_details:dict=Depends(AccessTokenBearer())):
    jti = token_details['jti']


    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={
            "message":"logged our successfully"
        },
        status_code=200
    )

@auth_router.post("password-reset-request")
async def password_reset_request(email_data:PasswordResetRequestModel,session:AsyncSession=Depends(get_session)):
    email = email_data.email

    token = create_url_safe_token({"email":email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

    html_message =f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a>to reset your password</p>
    """
    message = create_message(
        recipients=[email],
        subject="Reset Your Password",
        body=html_message
    )
    await mail.send_message(message)

    return JSONResponse(content={"message":"Please check your email for instructions to reset your password"
            },status_code=200)



@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(token:str,passwords:PasswordResetConfirmModel,session:AsyncSession=Depends(get_session)):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password
    if new_password !=confirm_password:
        raise HTTPException(status_code=400,detail="Passwords do not match")
    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')

    if user_email:
        user = await user_service.get_user_by_email(user_email,session)
        
        if not user:
            raise UserNotFound()

        passwd_hash = generate_passwd_hash(password=new_password)

        await user_service.update_user(user,{"password_hash":passwd_hash},session)

        return JSONResponse(content={
            "message":"Successfully reset"
        },status_code=200)
    return JSONResponse(content={
        "message":"Error occured during password reset."
    },status_code=400)
