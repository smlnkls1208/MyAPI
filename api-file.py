from fastapi import HTTPException , UploadFile, File
from pydantic import BaseModel
from fastapi import FastAPI, Response, Request, status, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Optional, List
import uuid
app = FastAPI()

class RegisterUser(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str


class LoginUser(BaseModel):
    email: str
    password: str

# обработка ошибок
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        field = error["loc"][-1]
        msg = f"field {field} {error['msg']}"
        if field not in errors:
            errors[field] = []
        errors[field].append(msg)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": 422,
            "message": errors
        }
    )


# 1. Регистрация
@app.post("/api-file/registration", status_code=201)
async def registration(data: dict):
    return {
        "success": True,
        "code": 201,
        "message": "Success",
        "token": "super-secret-bearer-token"
    }


# 2. Авторизация
@app.post("/api-file/authorization", status_code=200)
async def authorization(user: LoginUser):
    if user.email == "admin@admin.ru" and user.password == "Qa1":
        return {
            "success": True,
            "code": 200,
            "message": "Success",
            "token": "fake-jwt-token-123"
        }
    return JSONResponse(
        status_code=401,
        content={"success": False, "code": 401, "message": "Authorization failed"}
    )


# 3. Выход
@app.get("/api-file/logout", status_code=204)
async def logout(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail={"message": "Login failed"})
    return Response(status_code=204)

#настройка файла
ALLOWED_EXTENSIONS = {'doc', 'pdf', 'docx', 'zip', 'jpeg', 'jpg', 'png'}
MAX_FILE_SIZE = 2 * 1024 * 1024


# 4. Загрузка файлов
@app.post("/api-file/files", status_code=200)
async def upload_files(files: List[UploadFile] = File(...), authorization: Optional[str] = Header(None)):
    if not authorization:
        return JSONResponse(status_code=403, content={"message": "Login failed"})

    results = []

    for file in files:

        ext = file.filename.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "success": False,
                "message": [f"File type '{ext}' is not allowed"],
                "name": file.filename
            })
            continue

        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            results.append({
                "success": False,
                "message": ["File size exceeds 2 MB"],
                "name": file.filename
            })
            continue
        await file.seek(0)
        file_id = str(uuid.uuid4())[:10]

        # Успешный результат
        results.append({
            "success": True,
            "code": 200,
            "message": "Success",
            "name": file.filename,
            "url": f"http://127.0.0.1:8000/api-file/files/{file_id}",
            "file_id": file_id
        })

    return results


# 5. Просмотр файлов для пользователя
@app.get("/api-file/files/disk", status_code=200)
async def get_disk(authorization: Optional[str] = Header(None)):
    if not authorization:
        return Response(status_code=403, content='{"message": "Login failed"}')

    return [
        {
            "file_id": "qweasd1234",
            "name": "My_Resume.pdf",
            "code": 200,
            "url": "http://127.0.0.1:8000/api-file/files/qweasd1234",
            "accesses": [{"fullname": "Nikita", "email": "admin@admin.ru", "type": "author"}]
        }
    ]

# 2. Ошибка 404
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "message": "Not found",
            "code": 404
        }
    )

# 3. защищенный контент (403)
@app.get("/api-file/files/disk")
async def get_disk(authorization: Optional[str] = Header(None)):
    if not authorization or "Bearer" not in authorization:
        return JSONResponse(
            status_code=403,
            content={"message": "Login failed"}
        )
    return [{"file_id": "1234567890", "name": "test.txt"}]