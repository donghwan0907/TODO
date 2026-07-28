from fastapi import Request, Depends, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from schemas import UserCreate, UserLogin, MemoCreate, MemoUpdate
from sqlalchemy.orm import Session
from models import User, Memo
from dependencies import get_password_hash, verify_password, get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
def read_root(request: Request): 
    return templates.TemplateResponse(request, "home.html")

@router.get("/signup")
def read_signup(request: Request):
    return templates.TemplateResponse(request, "signup.html")

# 회원가입
@router.post("/signup")
def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        username=signup_data.username, 
        email = signup_data.email, 
        hashed_password = get_password_hash(signup_data.password)
    )
    db.add(new_user)
    db.commit() 
    db.refresh(new_user) 
    return new_user
   
# 로그인
@router.post("/login")
def login(
    request: Request, signin_data: UserLogin, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == signin_data.username).first()
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        print(request.session)
        return {"message": "로그인이 성공했습니다."}

@router.get("/login")
def read_login(request: Request):
    return templates.TemplateResponse(request, "login.html")

# 로그아웃
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

# 메모생성
@router.post("/memos")
async def create_memo(request: Request, db: Session = Depends(get_db)):

    username = request.session.get("username")
    if username is None: 
        raise HTTPException(status_code=401, detail="허가되지 않았습니다.")

    user = db.query(User).filter(User.username == username).first()
    if user is None: 
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
        title = data.get("title", "")
        content = data.get("content", "")
    else:
        form = await request.form()
        title = form.get("title", "")
        content = form.get("content", "")

    new_memo = Memo(user_id = user.id, title=title, content=content)
    db.add(new_memo)
    db.commit()
    db.refresh(new_memo)

    if "application/json" in content_type:
        return new_memo

    return RedirectResponse(url="/memos", status_code=303)

# 메모 글쓰기
@router.get("/write")
def memo_write(request: Request): 
    return templates.TemplateResponse(request, "write.html")

# 메모조회
@router.get("/memos")
def read_memos(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None: 
        raise HTTPException(status_code=401, detail="허가되지 않았습니다.")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    
    memos = db.query(Memo).filter(Memo.user_id == user.id).all()
    accept_header = request.headers.get("accept", "")

    if "application/json" in accept_header:
        return [
            {"title": memo.title, "content": memo.content} for memo in memos
        ]

    return templates.TemplateResponse(request, "memos.html", {"memos": memos})

# 메모수정
@router.put("/memos/{item_id}")
def update_memo(request: Request, item_id: int, memo:MemoUpdate, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None: 
        raise HTTPException(status_code=401, detail="허가되지 않았습니다.")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    
    db_memo = db.query(Memo).filter(Memo.user_id == user.id, Memo.id == item_id).first()

    if db_memo is None:
        return {"error": "메모를 찾을 수 없습니다."}

    if memo.title is not None:
        db_memo.title = memo.title
    if memo.content is not None:
        db_memo.content = memo.content

    db.commit()
    db.refresh(db_memo)

    return db_memo


# 메모삭제
@router.delete("/memos/{item_id}")
def delete_memo(request: Request, item_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if username is None: 
        raise HTTPException(status_code=401, detail="허가되지 않았습니다.")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")


    db_memo = db.query(Memo).filter(Memo.user_id == user.id, Memo.id == item_id).first()

    if db_memo is None:
        return {
            "error" : "메모를 찾을 수 없습니다."
        }

    db.delete(db_memo)
    db.commit()

    return {
        "message": "메모를 삭제했습니다"
    }