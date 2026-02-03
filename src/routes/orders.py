from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/amazon", tags=["orders"])


@router.post("/orders/file")
async def parse_amazon_orders_file(file: UploadFile):
    contents = await file.read()
    print("contents =", contents)
    await file.close()
    return {"filename": file.filename}
