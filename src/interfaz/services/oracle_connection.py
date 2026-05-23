import os
import oracledb

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_connection():

    raiz = Path(__file__).resolve().parent.parent.parent.parent

    wallet_dir = str(raiz / "wallet")

    os.environ["TNS_ADMIN"] = wallet_dir

    connection = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn="pipelinehibridohospital_high",
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=os.getenv("DB_PASSWORD")
    )

    return connection