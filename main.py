from fastapi import FastAPI, Request, HTTPException, status
from tortoise.contrib.fastapi import register_tortoise
from models import *
from authentication import get_password_hash, verify_token


from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from emails import send_email

# signals
from tortoise.signals import  post_save 
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient






app = FastAPI()




@app.get("/")
def index():
    return{"Message": "HelloWorld!"}





# process signals here
@post_save(User)
async def create_business(
    sender: "Type[User]",
    instance: User,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str]) -> None:
    
    if created:
        business_obj = await Business.create(
                business_name = instance.username, owner = instance)
        await business_pydantic.from_tortoise_orm(business_obj)
        # send email functionality
        await send_email([instance.email], instance)




@app.post('/registration')
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset = True)
    user_info['password'] = get_password_hash(user_info['password'])
    user_obj = await User.create(**user_info)   # store in db
    new_user = await user_pydantic.from_tortoise_orm(user_obj)  #create pydantic obj
 
    return {"status" : "ok", 
            "data" : 
                f"Hello {new_user.username} thanks for choosing our services. Please check your email inbox and click on the link to confirm your registration."}




templates = Jinja2Templates(directory="templates")


@app.get('/verification', response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    user = await verify_token(token)

    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html", {"request": request, "username": user.username})
    

    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED, 
            detail = "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )



# Register pydantic models
register_tortoise(
    app,
    db_url='sqlite://database.sqlite3',
    modules={'models' : ['models']},
    generate_schemas=True,
    add_exception_handlers=True
)