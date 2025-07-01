import os

import uvicorn


def main():
    """
    This is the entry point for the 'start-backend' script.
    It launches the Uvicorn server, binding to the host and port
    specified in the environment variables, with sensible defaults.
    """
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
