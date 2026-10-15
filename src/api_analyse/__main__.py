from multiprocessing import freeze_support

from api_analyse.main import app

if __name__ == "__main__":
    freeze_support()
    app()
