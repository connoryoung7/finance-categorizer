from fastapi import FastAPI, File, UploadFile

app = FastAPI()

def main():
    print("Hello from backend!")

if __name__ == "__main__":
    main()

@app.post("/amazon/orders/file")
async def parse_amazon_orders_file(file: UploadFile):
    contents = await file.read()
    print("contents =", contents)
    await file.close()
    return {"filename": file.filename}
