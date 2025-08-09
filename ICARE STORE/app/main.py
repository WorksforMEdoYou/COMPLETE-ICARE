from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .routers import token, category, store, distributor, manufacturer, product, purchase, pricing, orders, stocks, sales
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from .db.mongodb import connect_to_mongodb
from .db.mysql import init_db
import logging
from .firebase_config import initialize_firebase_app
from fastapi.security import APIKeyHeader

# Security schemes for custom headers
access_token_scheme = APIKeyHeader(name="Authorization", auto_error=False)
refresh_token_scheme = APIKeyHeader(name="X-Refresh-Token", auto_error=False)

def get_current_user(
    access_token: str = Depends(access_token_scheme),
    refresh_token: str = Depends(refresh_token_scheme)
):
    # Example logic: require at least access_token
    if not access_token:
        raise StarletteHTTPException(status_code=401, detail="Access token missing")
    # You can add your JWT validation logic here
    return {"access_token": access_token, "refresh_token": refresh_token}

app = FastAPI(
    title="Istore API",
    description="API for managing Istore operations",
    version="1.0.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
        "scopes": [],
    },
    openapi_tags=[
        {"name": "Token", "description": "Operations with access and refresh tokens"}
    ],
    openapi_components={
        "securitySchemes": {
            "AccessToken": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Enter your **Access Token** (e.g., **Bearer eyJ...**)"
            },
            "RefreshToken": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Refresh-Token",
                "description": "Enter your **Refresh Token**"
            }
        }
    }
)

# Custom JSON encoder for ObjectId
def json_encoder(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Override default JSONEncoder with custom JSONEncoder
app.json_encoder = json_encoder

#MySql Routers

app.include_router(category.router, prefix="/storeapi", tags=["Category"])
app.include_router(store.router, prefix="/storeapi", tags=["Store"])
app.include_router(distributor.router, prefix="/storeapi", tags=["Distributor"])
app.include_router(manufacturer.router, prefix="/storeapi", tags=["Manufacturer"])
app.include_router(product.router, prefix="/storeapi", tags=["product Master"])

#MongoDB Routers

app.include_router(purchase.router, prefix="/storeapi", tags=["Purchase"])
app.include_router(pricing.router, prefix="/storeapi", tags=["Pricing"])
app.include_router(orders.router, prefix="/storeapi", tags=["Orders"])
app.include_router(stocks.router, prefix="/storeapi", tags=["Stocks"])
app.include_router(sales.router, prefix="/storeapi", tags=["Sales"])

# Token Router
app.include_router(token.router, prefix="/storeapi", tags=["Token"])

#App Health Checkup
@app.get("/health", tags=["Health"], description="Operation related to health")
def health_check():
    return {"status": "healthy"}

# Startup Event
@app.on_event("startup")
async def on_startup():
    logger.info("App is starting...")
    await init_db() #connectiing the mysql database
    await connect_to_mongodb() #connecting the mongoDB database
    await initialize_firebase_app() #initializing the firebase app
    logger.info("App started successfully.")
    
# Initialize database connection
@app.get("/")
def read_root():
    return {"message": "Welcome to the Istore"}

# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )
