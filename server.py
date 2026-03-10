from app import create_app
import os
import uvicorn

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5025))
    print(f"Server running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
